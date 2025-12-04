import chainlit as cl
import json
import uuid
from src.database.db_manager import initialize_database, update_session_state
from src.agents.router_agent import RouterAgent
from src.agents.filing_workflow_agent import FilingWorkflowAgentADK as FilingWorkflowAgent
from src.agents.query_agent import answer_tax_question
from src.tools.guardrails.validation_tools import detect_prompt_injection, emergency_audit_sanitizer

router = RouterAgent()
filing_agent = FilingWorkflowAgent()

@cl.on_chat_start
async def start():
    """Initialize chat session"""
    try:
        initialize_database()
    except:
        pass
    
    session_id = str(uuid.uuid4())
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("filing_started", False)
    cl.user_session.set("filing_type", None)
    cl.user_session.set("current_section", None)
    cl.user_session.set("collected_data", {})
    cl.user_session.set("current_question_index", 0)
    cl.user_session.set("pending_sections", [])  # Track sections that need to be asked
    
    welcome_message = router.get_greeting_message()
    await cl.Message(content=welcome_message).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle user messages"""
    user_input = message.content
    
    injection_check = detect_prompt_injection(user_input)
    if not injection_check['safe']:
        await cl.Message(content="⚠️ Invalid input detected. Please provide valid information.").send()
        return
    
    filing_started = cl.user_session.get("filing_started")
    
    if not filing_started:
        intent = router.detect_intent(user_input)
        workflow = router.route_to_workflow(intent)
        
        if workflow == "greeting_response":
            response = router.get_greeting_message()
            await cl.Message(content=response).send()
            return
        
        if workflow == "help_response":
            # If the user actually asked a question (e.g. "I have a question about income tax"),
            # call Gemini to answer it. Otherwise, show the generic help message.
            lower_input = user_input.lower()
            if any(k in lower_input for k in ["question", "?", "how ", "what ", "why ", "explain", "clarify"]):
                # Stream Gemini answer so the user sees tokens as they arrive
                session_id = cl.user_session.get("session_id") or "anonymous"
                raw_answer = answer_tax_question(session_id, user_input)

                msg = cl.Message(content="")
                await msg.send()
                for line in raw_answer.split("\n"):
                    await msg.stream_token(line + "\n")
            else:
                response = router.get_help_message()
                await cl.Message(content=response).send()
            return
        
        if workflow == "clarification_needed":
            response = router.get_clarification_message()
            await cl.Message(content=response).send()
            return
        
        if workflow == "filing_workflow":
            filing_type = intent.get('filing_type')
            
            if filing_type == "IT1":
                cl.user_session.set("filing_started", True)
                cl.user_session.set("filing_type", "IT1")
                cl.user_session.set("current_section", "A_PART1")
                
                section_result = filing_agent.process_section_a_part1(cl.user_session.get("session_id"))
                section_data = section_result['data']
                
                cl.user_session.set("current_section_data", section_data)
                cl.user_session.set("section_responses", {})
                
                first_question = section_data['questions'][0]
                await cl.Message(content=section_result['message']).send()
                await cl.Message(content=f"**Question 1/12:** {first_question['text']}").send()
                return
            
            elif filing_type == "VAT3":
                cl.user_session.set("filing_started", True)
                cl.user_session.set("filing_type", "VAT3")
                cl.user_session.set("current_section", "VAT_A")

                section_result = filing_agent.process_vat3_section_a(cl.user_session.get("session_id"))
                section_data = section_result['data']

                cl.user_session.set("current_section_data", section_data)
                cl.user_session.set("section_responses", {})

                first_question = section_data['questions'][0]
                await cl.Message(content=section_result['message']).send()
                await cl.Message(content=first_question['text']).send()
                return
            
            else:
                await cl.Message(content="Please specify: IT1 or VAT3?").send()
                return
    
    else:
        current_section = cl.user_session.get("current_section")
        section_data = cl.user_session.get("current_section_data")
        section_responses = cl.user_session.get("section_responses", {})
        question_index = cl.user_session.get("current_question_index", 0)
        collected_data = cl.user_session.get("collected_data", {})
        filing_type = cl.user_session.get("filing_type")
        
        current_question = filing_agent.get_next_question(
            current_section,
            section_data,
            section_responses
        )
        
        if current_question:
            field_name = current_question['field']
            
            validation_result = filing_agent.validate_response(field_name, user_input)
            
            if not validation_result.get('valid', True):
                error_message = validation_result.get('error', 'Invalid input')
                await cl.Message(content=f"❌ {error_message}. Please try again.").send()
                await cl.Message(content=current_question['text']).send()
                return
            
            validated_value = validation_result.get('value', user_input)
            section_responses[field_name] = validated_value
            
            if current_section not in collected_data:
                collected_data[current_section] = {}
            collected_data[current_section][field_name] = validated_value
            
            cl.user_session.set("section_responses", section_responses)
            cl.user_session.set("collected_data", collected_data)
            
            session_id = cl.user_session.get("session_id")
            kra_pin = collected_data.get('A_PART1', {}).get('kra_pin', 'UNKNOWN')

            # Persist response tagged with the active filing type
            filing_agent.save_response(
                kra_pin,
                filing_type or "UNKNOWN",
                current_section,
                field_name,
                str(validated_value),
                session_id
            )
            
            next_question = filing_agent.get_next_question(
                current_section,
                section_data,
                section_responses
            )
            
            if next_question:
                question_index += 1
                cl.user_session.set("current_question_index", question_index)
                
                if current_section == "A_PART1":
                    await cl.Message(content=f"**Question {question_index + 1}/12:** {next_question['text']}").send()
                else:
                    await cl.Message(content=next_question['text']).send()
            else:
                # ===== IT1 WORKFLOW SECTION-TO-SECTION TRANSITIONS =====
                if current_section == "A_PART1" and filing_type == "IT1":
                    # Move from A Part 1 -> A Part 2 (Bank details)
                    cl.user_session.set("current_section", "A_PART2")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_section_a_part2(session_id)
                    section_data = section_result["data"]

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data["questions"][0]
                    await cl.Message(content="✅ Section A Part 1 completed!").send()
                    await cl.Message(content=section_result["message"]).send()
                    await cl.Message(content=first_question["text"]).send()

                elif current_section == "A_PART2" and filing_type == "IT1":
                    # A Part 2 -> A Part 3 (Auditor details)
                    cl.user_session.set("current_section", "A_PART3")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_section_a_part3(session_id)
                    section_data = section_result["data"]

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data["questions"][0]
                    await cl.Message(content="✅ Section A Part 2 completed!").send()
                    await cl.Message(content=section_result["message"]).send()
                    await cl.Message(content=first_question["text"]).send()

                elif current_section == "A_PART3" and filing_type == "IT1":
                    # A Part 3 -> A Part 6 (if disability) else -> Section F
                    a_part1_data = collected_data.get("A_PART1", {})
                    has_disability = a_part1_data.get("has_disability", "").strip().lower() == "yes"

                    if has_disability:
                        cl.user_session.set("current_section", "A_PART6")
                        cl.user_session.set("current_question_index", 0)

                        section_result = filing_agent.process_section_a_part6(session_id)
                        section_data = section_result["data"]

                        cl.user_session.set("current_section_data", section_data)
                        cl.user_session.set("section_responses", {})

                        first_question = section_data["questions"][0]
                        await cl.Message(content="✅ Section A Part 3 completed!").send()
                        await cl.Message(content=section_result["message"]).send()
                        await cl.Message(content=first_question["text"]).send()
                    else:
                        # Go straight to Section F (Employment income)
                        cl.user_session.set("current_section", "F")
                        cl.user_session.set("current_question_index", 0)

                        section_result = filing_agent.process_section_f(session_id, collected_data)
                        section_data = section_result["data"]

                        cl.user_session.set("current_section_data", section_data)
                        cl.user_session.set("section_responses", {})

                        first_question = section_data["questions"][0]
                        await cl.Message(content="✅ Section A completed!").send()
                        await cl.Message(content=section_result["message"]).send()
                        await cl.Message(content=first_question["text"]).send()

                elif current_section == "A_PART6" and filing_type == "IT1":
                    # A Part 6 (disability) -> Section F
                    cl.user_session.set("current_section", "F")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_section_f(session_id, collected_data)
                    section_data = section_result["data"]

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data["questions"][0]
                    await cl.Message(content="✅ Section A completed!").send()
                    await cl.Message(content=section_result["message"]).send()
                    await cl.Message(content=first_question["text"]).send()

                elif current_section == "F" and filing_type == "IT1":
                    # Section F -> Section M (if employment income) else F2
                    f_data = collected_data.get("F", {})
                    has_employment_income = f_data.get("has_employment_income", "").strip().lower() == "yes"

                    if has_employment_income:
                        cl.user_session.set("current_section", "M")
                        cl.user_session.set("current_question_index", 0)

                        section_result = filing_agent.process_section_m_paye(session_id, collected_data)
                        section_data = section_result["data"]

                        cl.user_session.set("current_section_data", section_data)
                        cl.user_session.set("section_responses", {})

                        first_question = section_data["questions"][0]
                        await cl.Message(content="✅ Section F completed!").send()
                        await cl.Message(content=section_result["message"]).send()
                        await cl.Message(content=first_question["text"]).send()
                    else:
                        # Skip PAYE if no employment income, go to F2
                        cl.user_session.set("current_section", "F2")
                        cl.user_session.set("current_question_index", 0)

                        section_result = filing_agent.process_section_f2_other_income(session_id, collected_data)
                        section_data = section_result["data"]

                        cl.user_session.set("current_section_data", section_data)
                        cl.user_session.set("section_responses", {})

                        first_question = section_data["questions"][0]
                        await cl.Message(content="✅ Section F completed!").send()
                        await cl.Message(content=section_result["message"]).send()
                        await cl.Message(content=first_question["text"]).send()

                elif current_section == "M" and filing_type == "IT1":
                    # M (PAYE) -> F2 (other income)
                    cl.user_session.set("current_section", "F2")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_section_f2_other_income(session_id, collected_data)
                    section_data = section_result["data"]

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data["questions"][0]
                    await cl.Message(content="✅ Section M (PAYE) completed!").send()
                    await cl.Message(content=section_result["message"]).send()
                    await cl.Message(content=first_question["text"]).send()

                elif current_section == "F2" and filing_type == "IT1":
                    # F2 -> H (estate/trust)
                    cl.user_session.set("current_section", "H")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_section_h_estate_trust(session_id, collected_data)
                    section_data = section_result["data"]

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data["questions"][0]
                    await cl.Message(content="✅ Section F2 completed!").send()
                    await cl.Message(content=section_result["message"]).send()
                    await cl.Message(content=first_question["text"]).send()

                elif current_section == "H" and filing_type == "IT1":
                    # H -> K (HOSP)
                    cl.user_session.set("current_section", "K")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_section_k_hosp(session_id, collected_data)
                    section_data = section_result["data"]

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data["questions"][0]
                    await cl.Message(content="✅ Section H completed!").send()
                    await cl.Message(content=section_result["message"]).send()
                    await cl.Message(content=first_question["text"]).send()

                elif current_section == "K" and filing_type == "IT1":
                    # K -> N (installment tax)
                    cl.user_session.set("current_section", "N")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_section_n_installment_tax(session_id, collected_data)
                    section_data = section_result["data"]

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data["questions"][0]
                    await cl.Message(content="✅ Section K completed!").send()
                    await cl.Message(content=section_result["message"]).send()
                    await cl.Message(content=first_question["text"]).send()

                elif current_section == "N" and filing_type == "IT1":
                    # N -> O (WHT)
                    cl.user_session.set("current_section", "O")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_section_o_wht(session_id, collected_data)
                    section_data = section_result["data"]

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data["questions"][0]
                    await cl.Message(content="✅ Section N completed!").send()
                    await cl.Message(content=section_result["message"]).send()
                    await cl.Message(content=first_question["text"]).send()

                elif current_section == "O" and filing_type == "IT1":
                    # O -> P (advance tax on vehicles)
                    cl.user_session.set("current_section", "P")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_section_p_advance_tax(session_id, collected_data)
                    section_data = section_result["data"]

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data["questions"][0]
                    await cl.Message(content="✅ Section O completed!").send()
                    await cl.Message(content=section_result["message"]).send()
                    await cl.Message(content=first_question["text"]).send()

                elif current_section == "P" and filing_type == "IT1":
                    # P -> Q (income tax paid in advance)
                    cl.user_session.set("current_section", "Q")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_section_q_income_tax_paid(session_id, collected_data)
                    section_data = section_result["data"]

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data["questions"][0]
                    await cl.Message(content="✅ Section P completed!").send()
                    await cl.Message(content=section_result["message"]).send()
                    await cl.Message(content=first_question["text"]).send()

                elif current_section == "Q" and filing_type == "IT1":
                    # After Q: handle conditional J, L, R, then compute tax
                    a_part1_data = collected_data.get("A_PART1", {})
                    pending_sections = []

                    # Check for mortgage (Section J)
                    if a_part1_data.get("has_mortgage", "").strip().lower() == "yes":
                        if "J" not in collected_data:
                            pending_sections.append("J")

                    # Check for insurance (Section L)
                    if a_part1_data.get("has_insurance", "").strip().lower() == "yes":
                        if "L" not in collected_data:
                            pending_sections.append("L")

                    # Check for foreign income (Section R)
                    if a_part1_data.get("has_foreign_income", "").strip().lower() == "yes":
                        if "R" not in collected_data:
                            pending_sections.append("R")

                    if pending_sections:
                        next_section = pending_sections[0]
                        cl.user_session.set("pending_sections", pending_sections[1:])
                        cl.user_session.set("current_section", next_section)
                        cl.user_session.set("current_question_index", 0)

                        if next_section == "J":
                            section_result = filing_agent.process_section_j_mortgage(session_id, collected_data)
                        elif next_section == "L":
                            section_result = filing_agent.process_section_l_insurance(session_id, collected_data)
                        elif next_section == "R":
                            section_result = filing_agent.process_section_r_dtaa(session_id, collected_data)

                        section_data = section_result["data"]
                        cl.user_session.set("current_section_data", section_data)
                        cl.user_session.set("section_responses", {})

                        first_question = section_data["questions"][0]
                        await cl.Message(content="✅ Section Q completed!").send()
                        await cl.Message(content=section_result["message"]).send()
                        await cl.Message(content=first_question["text"]).send()
                    else:
                        # No more sections, compute tax
                        await cl.Message(content="✅ All sections completed! Computing your tax...").send()

                        computation = filing_agent.compute_final_tax(collected_data)
                        result = computation["computation"]

                        summary = f"""
**📊 Tax Computation Summary**

💰 Tax before reliefs: KES {result['tax_payable']:,.2f}
🎯 Total reliefs applied (personal + insurance): KES {(result['tax_payable'] - result['tax_after_reliefs']):,.2f}
📉 Tax after reliefs: KES {result['tax_after_reliefs']:,.2f}
🏦 Tax already paid / credits: KES {result['total_credits']:,.2f}

**Final position: KES {abs(result['final_tax_due_or_refund']):,.2f}**
Status: {'✅ TAX DUE (amount to pay)' if result['status'] == 'TAX_DUE' else '✨ REFUND DUE (amount to be refunded)'}

Thank you for filing your IT1 return!
"""
                        # Stream the summary for a smoother UX
                        msg = cl.Message(content="")
                        await msg.send()
                        for line in summary.split("\n"):
                            await msg.stream_token(line + "\n")

                        kra_pin = collected_data.get("A_PART1", {}).get("kra_pin")
                        declared_income = result["total_income"]

                        filing_agent.trigger_background_audit(kra_pin, declared_income)

                        cl.user_session.set("filing_started", False)
                        cl.user_session.set("collected_data", {})

                elif current_section == "VAT_A" and filing_type == "VAT3":
                    # VAT_A -> VAT_B (16% sales)
                    cl.user_session.set("current_section", "VAT_B")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_vat3_section_b(session_id, collected_data)
                    section_data = section_result['data']

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data['questions'][0]
                    await cl.Message(content="✅ VAT3 Section A completed!").send()
                    await cl.Message(content=section_result['message']).send()
                    await cl.Message(content=first_question['text']).send()

                elif current_section == "VAT_B" and filing_type == "VAT3":
                    # VAT_B -> VAT_C (8% sales)
                    cl.user_session.set("current_section", "VAT_C")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_vat3_section_c(session_id, collected_data)
                    section_data = section_result['data']

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data['questions'][0]
                    await cl.Message(content="✅ VAT3 Section B completed!").send()
                    await cl.Message(content=section_result['message']).send()
                    await cl.Message(content=first_question['text']).send()

                elif current_section == "VAT_C" and filing_type == "VAT3":
                    # VAT_C -> VAT_D (Zero-rated sales)
                    cl.user_session.set("current_section", "VAT_D")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_vat3_section_d(session_id, collected_data)
                    section_data = section_result['data']

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data['questions'][0]
                    await cl.Message(content="✅ VAT3 Section C completed!").send()
                    await cl.Message(content=section_result['message']).send()
                    await cl.Message(content=first_question['text']).send()

                elif current_section == "VAT_D" and filing_type == "VAT3":
                    # VAT_D -> VAT_E (Exempt sales)
                    cl.user_session.set("current_section", "VAT_E")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_vat3_section_e(session_id, collected_data)
                    section_data = section_result['data']

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data['questions'][0]
                    await cl.Message(content="✅ VAT3 Section D completed!").send()
                    await cl.Message(content=section_result['message']).send()
                    await cl.Message(content=first_question['text']).send()

                elif current_section == "VAT_E" and filing_type == "VAT3":
                    # VAT_E -> VAT_F (16% purchases)
                    cl.user_session.set("current_section", "VAT_F")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_vat3_section_f(session_id, collected_data)
                    section_data = section_result['data']

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data['questions'][0]
                    await cl.Message(content="✅ VAT3 Section E completed!").send()
                    await cl.Message(content=section_result['message']).send()
                    await cl.Message(content=first_question['text']).send()

                elif current_section == "VAT_F" and filing_type == "VAT3":
                    # VAT_F -> VAT_G (8% purchases)
                    cl.user_session.set("current_section", "VAT_G")
                    cl_user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_vat3_section_g(session_id, collected_data)
                    section_data = section_result['data']

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data['questions'][0]
                    await cl.Message(content="✅ VAT3 Section F completed!").send()
                    await cl.Message(content=section_result['message']).send()
                    await cl.Message(content=first_question['text']).send()

                elif current_section == "VAT_G" and filing_type == "VAT3":
                    # VAT_G -> VAT_H (Zero-rated purchases)
                    cl.user_session.set("current_section", "VAT_H")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_vat3_section_h(session_id, collected_data)
                    section_data = section_result['data']

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data['questions'][0]
                    await cl.Message(content="✅ VAT3 Section G completed!").send()
                    await cl.Message(content=section_result['message']).send()
                    await cl.Message(content=first_question['text']).send()

                elif current_section == "VAT_H" and filing_type == "VAT3":
                    # VAT_H -> VAT_I (Exempt purchases)
                    cl.user_session.set("current_section", "VAT_I")
                    cl.user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_vat3_section_i(session_id, collected_data)
                    section_data = section_result['data']

                    cl.user_session.set("current_section_data", section_data)
                    cl.user_session.set("section_responses", {})

                    first_question = section_data['questions'][0]
                    await cl.Message(content="✅ VAT3 Section H completed!").send()
                    await cl.Message(content=section_result['message']).send()
                    await cl.Message(content=first_question['text']).send()

                elif current_section == "VAT_I" and filing_type == "VAT3":
                    # VAT_I -> VAT_J (Imported services)
                    cl.user_session.set("current_section", "VAT_J")
                    cl_user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_vat3_section_j(session_id, collected_data)
                    section_data = section_result['data']

                    cl_user_session.set("current_section_data", section_data)
                    cl_user_session.set("section_responses", {})

                    first_question = section_data['questions'][0]
                    await cl.Message(content="✅ VAT3 Section I completed!").send()
                    await cl.Message(content=section_result['message']).send()
                    await cl.Message(content=first_question['text']).send()

                elif current_section == "VAT_J" and filing_type == "VAT3":
                    # VAT_J -> VAT_K (VAT paid in advance)
                    cl_user_session.set("current_section", "VAT_K")
                    cl_user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_vat3_section_k(session_id, collected_data)
                    section_data = section_result['data']

                    cl_user_session.set("current_section_data", section_data)
                    cl_user_session.set("section_responses", {})

                    first_question = section_data['questions'][0]
                    await cl.Message(content="✅ VAT3 Section J completed!").send()
                    await cl.Message(content=section_result['message']).send()
                    await cl.Message(content=first_question['text']).send()

                elif current_section == "VAT_K" and filing_type == "VAT3":
                    # VAT_K -> VAT_L (Withholding VAT certificates)
                    cl_user_session.set("current_section", "VAT_L")
                    cl_user_session.set("current_question_index", 0)

                    section_result = filing_agent.process_vat3_section_l(session_id, collected_data)
                    section_data = section_result['data']

                    cl_user_session.set("current_section_data", section_data)
                    cl_user_session.set("section_responses", {})

                    first_question = section_data['questions'][0]
                    await cl.Message(content="✅ VAT3 Section K completed!").send()
                    await cl.Message(content=section_result['message']).send()
                    await cl.Message(content=first_question['text']).send()

                elif current_section == "VAT_L" and filing_type == "VAT3":
                    # Final VAT3 computation after all sections
                    await cl.Message(content="✅ VAT3 Section L completed! Computing your VAT...").send()

                    computation = filing_agent.compute_vat3(collected_data)
                    result = computation["calculation"]

                    summary = f"""
**📊 VAT3 Calculation Summary**

Output VAT: KES {result['output_vat']:,.2f}
Input VAT: KES {result['input_vat']:,.2f}
Deductible Input VAT: KES {result['deductible_input_vat']:,.2f}
WHT Credits: KES {result['wht_credits']:,.2f}
VAT Paid: KES {result['vat_paid']:,.2f}

**Net VAT: KES {abs(result['net_vat_payable_credit']):,.2f}**
Status: {'✅ VAT PAYABLE' if result['status'] == 'VAT_PAYABLE' else '✨ CREDIT CARRIED FORWARD'}

Thank you for filing your VAT3 return!
"""
                    await cl.Message(content=summary).send()

                    cl.user_session.set("filing_started", False)
                    cl_user_session.set("collected_data", {})

                elif current_section in ["J", "L", "R"] and filing_type == "IT1":
                    # Handle conditional sections (J, L, R)
                    # Check if there are more pending sections
                    pending_sections = cl.user_session.get("pending_sections", [])
                    
                    if pending_sections:
                        # Move to next pending section
                        next_section = pending_sections[0]
                        cl.user_session.set("pending_sections", pending_sections[1:])
                        cl.user_session.set("current_section", next_section)
                        cl.user_session.set("current_question_index", 0)
                        
                        if next_section == "J":
                            section_result = filing_agent.process_section_j_mortgage(session_id, collected_data)
                        elif next_section == "L":
                            section_result = filing_agent.process_section_l_insurance(session_id, collected_data)
                        elif next_section == "R":
                            section_result = filing_agent.process_section_r_dtaa(session_id, collected_data)
                        
                        section_data = section_result['data']
                        cl.user_session.set("current_section_data", section_data)
                        cl.user_session.set("section_responses", {})
                        
                        first_question = section_data['questions'][0]
                        section_name = {"J": "J (Mortgage)", "L": "L (Insurance)", "R": "R (Foreign Income)"}.get(next_section, next_section)
                        await cl.Message(content=f"✅ Section {section_name} completed!").send()
                        await cl.Message(content=section_result['message']).send()
                        await cl.Message(content=first_question['text']).send()
                    else:
                        # No more sections, compute tax
                        await cl.Message(content="✅ All sections completed! Computing your tax...").send()
                        
                        computation = filing_agent.compute_final_tax(collected_data)
                        result = computation['computation']
                        
                        summary = f"""
**📊 Tax Computation Summary**

💰 Total Income: KES {result['total_income']:,.2f}
📉 Taxable Income: KES {result['taxable_income']:,.2f}
💸 Tax Payable: KES {result['tax_payable']:,.2f}
🎯 Tax After Reliefs: KES {result['tax_after_reliefs']:,.2f}
🏦 Total Credits: KES {result['total_credits']:,.2f}

**Final Amount: KES {abs(result['final_tax_due_or_refund']):,.2f}**
Status: {'✅ TAX DUE' if result['status'] == 'TAX_DUE' else '✨ REFUND DUE'}

Thank you for filing your IT1 return!
"""
                        await cl.Message(content=summary).send()
                        
                        kra_pin = collected_data.get('A_PART1', {}).get('kra_pin')
                        declared_income = result['total_income']
                        
                        filing_agent.trigger_background_audit(kra_pin, declared_income)
                        
                        cl.user_session.set("filing_started", False)
                        cl.user_session.set("collected_data", {})
                
                elif current_section == "VAT_F" and filing_type == "VAT3":
                    await cl.Message(content="✅ VAT3 Section F completed! Computing your VAT...").send()

                    computation = filing_agent.compute_vat3(collected_data)
                    result = computation["calculation"]

                    summary = f"""
**📊 VAT3 Calculation Summary**

Output VAT: KES {result['output_vat']:,.2f}
Input VAT: KES {result['input_vat']:,.2f}
Deductible Input VAT: KES {result['deductible_input_vat']:,.2f}
WHT Credits: KES {result['wht_credits']:,.2f}
VAT Paid: KES {result['vat_paid']:,.2f}

**Net VAT: KES {abs(result['net_vat_payable_credit']):,.2f}**
Status: {'✅ VAT PAYABLE' if result['status'] == 'VAT_PAYABLE' else '✨ CREDIT CARRIED FORWARD'}

Thank you for filing your VAT3 return!
"""
                    await cl.Message(content=summary).send()

                    cl.user_session.set("filing_started", False)
                    cl.user_session.set("collected_data", {})

import datetime
import json
from enum import Enum
from typing import Dict, List, Optional
import redis  # For session management
from typer.cli import state


class ConversationState(Enum):
    GREETING = "greeting"
    QUERY_PROCESSING = "query_processing"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification_needed"
    COMPLETED = "completed"


class DialogueManager:
    def __init__(self, rule_engine, nlp_engine, response_generator):
        self.rule_engine = rule_engine
        self.nlp_engine = nlp_engine
        self.response_generator = response_generator
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.conversation_contexts = {}

    def process_message(self, user_id: str, session_id: str, message: str) -> Dict:
        """Process user message with context tracking"""

        print(f"\n=== DIALOGUE MANAGER PROCESSING ===")
        print(f"Message: '{message}'")

        print(f"self.response_generator exists: {hasattr(self, 'response_generator')}")
        print(f"self.response_generator type: {type(self.response_generator)}")

        # Get or create conversation context
        context_key = f"conv:{user_id}:{session_id}"
        context = self._get_context(context_key)



        # Step 1: Intent and Entity Extraction
        nlp_result = self.nlp_engine.process(message)

        # nlp_result = self.nlp_engine.analyze(message, context)

        if 'entities' not in nlp_result:
            nlp_result['entities'] = []

        nlp_result['entities'].append({
             'label': 'current_time',
             'text': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })



        intent = nlp_result.get('intent', 'unknown')
        confidence = nlp_result.get('confidence', 0.5)
        print(f"NLP Result keys: {nlp_result.keys()}")

        print(f"DEBUG: confidence type: {type(confidence)}, value: {confidence}")

        print(f"Intent: {intent}, Confidence: {confidence}")

        # Convert to float if needed
        if isinstance(confidence, (int, float)):
            conf_value = float(confidence)
        else:
            print(f"WARNING: confidence is not numeric: {confidence}")
            conf_value = 0.5  # Default

        # Now compare
        if conf_value < 0.5:
            print(f"DEBUG: Low confidence detected: {conf_value}")
            # Handle low confidence with ALL required arguments
            return self._handle_low_confidence(
                user_message=message,
                confidence=conf_value,
                context={'user_id': user_id, 'session_id': session_id}
            )

        processing_method = nlp_result.get('processing_method', 'hybrid')


        # Step 2: Check if rule-based response applies
        rule_response = self.rule_engine.match(message, nlp_result['intent'])

        # Step 3: Determine processing path (Hybrid Decision)
        if rule_response and rule_response['confidence'] > 0.9:
            # Use rule-based response
            processing_method = "rule_based"
            response_data = rule_response
        elif nlp_result['confidence'] > 0.7:
            # Use NLP-based response
            processing_method = "nlp_based"
            response_data = nlp_result
        else:
            # Fallback to clarification or knowledge base
            processing_method = "clarification"
            response_data = self._handle_low_confidence(message, context)

        # Step 4: Update conversation context
        self._update_context(context_key, {
            'last_intent': nlp_result['intent'],
            'last_entities': nlp_result['entities'],
            'conversation_history': context.get('history', []) + [message],
            'state': self._determine_state(user_id, session_id, intent, confidence, context)
        })

        # Step 5: Generate final response
        final_response = self.response_generator.generate(
            response_data,
            context,
            processing_method
        )

        # Step 6: Log interaction
        self._log_interaction(
            user_id=user_id, session_id=session_id, message=message, response=final_response,
            processing_method=processing_method, intent=intent, confidence=confidence, context=context
        )

        # Generate response
        print("Generating response...")
        response = self.response_generator.generate(
            response_data={
                'intent': intent,
                'confidence': confidence,
                'entities': nlp_result.get('entities', []),
                'text': message,
                # Include other NLP data if needed
                'original_text': nlp_result.get('original_text', message),
                'sentiment': nlp_result.get('sentiment', {}),
                'keywords': nlp_result.get('keywords', []),
                'tokens': nlp_result.get('tokens', []),
                'processed': nlp_result.get('processed', True)
            },
            context={'user_id': user_id, 'session_id': session_id},
            method='nlp_based'  # or whatever method you're using
        )
        print(f"Response generated: '{response[:50]}...'")

        # Get follow-ups
        print("Getting follow-ups...")
        follow_ups = self._suggest_follow_ups(intent,confidence,state,context)
        print(f"Follow-ups: {follow_ups}")

        return {
            'response': final_response,
            'confidence': response_data.get('confidence', 0.0),
            'processing_method': processing_method,
            'suggested_follow_ups': self._suggest_follow_ups(intent=intent,
            confidence=confidence,
            current_state=state,
            context=context),
            'context_id': context_key
        }

    def _get_context(self, context_key: str) -> Dict:
        """Retrieve conversation context from Redis"""
        context_data = self.redis_client.get(context_key)
        return json.loads(context_data) if context_data else {
            'history': [],
            'state': ConversationState.GREETING,
            'entities': {},
            'user_preferences': {}
        }

    def _update_context(self, context_key: str, updates: Dict):
        """Update conversation context"""
        current = self._get_context(context_key)
        current.update(updates)
        self.redis_client.setex(
            context_key,
            3600,  # 1 hour expiry
            json.dumps(current)
        )

    def _handle_low_confidence(self, user_message: str, confidence, context: Dict = None) -> Dict:
        """
        Handle cases where intent confidence is low
        """
        if context is None:
            context = {}

        # Ensure confidence is a float
        try:
            if isinstance(confidence, dict):
                # If confidence is a dict, try to extract a numeric value
                conf_value = confidence.get('score', confidence.get('confidence', 0.0))
            else:
                conf_value = float(confidence)
        except (ValueError, TypeError):
            conf_value = 0.0  # Default to low confidence

        # Different strategies based on confidence level
        if conf_value < 0.3:
            # Very low confidence - ask for clarification
            responses = [
                "I'm not quite sure what you mean. Could you rephrase that?",
                "I want to make sure I understand correctly. Could you say that differently?",
                "I'm having trouble understanding. Could you provide more details?"
            ]
            import random
            response = random.choice(responses)
            action = 'clarify'
            processing_method = 'low_confidence_clarification'  # ADD THIS

        elif conf_value < 0.5:
            # Medium-low confidence - offer suggestions
            responses = [
                "I think you might be asking about: (1) Library hours, (2) Finding books, or (3) Borrowing policies. Which one interests you?",
                "Could this be about: Library hours, Book search, or Borrowing information?",
                "I can help with library hours, book searches, or borrowing questions. Which would you like?"
            ]
            import random
            response = random.choice(responses)
            action = 'suggest'
            processing_method = 'medium_confidence_suggestion'  # ADD THIS

        else:
            # Confidence is okay, but we still want to verify
            responses = [
                f"Just to make sure I understood: are you asking about '{user_message}'?",
                f"I think you're asking about: {user_message}. Is that correct?",
                f"Let me confirm: you want to know about '{user_message}', right?"
            ]
            import random
            response = random.choice(responses)
            action = 'confirm'
            processing_method = 'high_confidence_confirmation'  # ADD THIS

        # Generate follow-up questions
        follow_ups = self._get_clarification_questions(user_message, conf_value)

        return {
            'response': response,
            'action': action,
            'confidence': conf_value,
            'processing_method': processing_method,  # ADD THIS LINE
            'requires_clarification': True,
            'suggested_follow_ups': follow_ups,
            'original_message': user_message
        }

    # def _handle_low_confidence(self, user_message: str, confidence, context: Dict = None) -> Dict:
    #     """
    #     Handle cases where intent confidence is low
    #     """
    #     if context is None:
    #         context = {}
    #
    #     # Ensure confidence is a float
    #     try:
    #         if isinstance(confidence, dict):
    #             # If confidence is a dict, try to extract a numeric value
    #             conf_value = confidence.get('score', confidence.get('confidence', 0.0))
    #         else:
    #             conf_value = float(confidence)
    #     except (ValueError, TypeError):
    #         conf_value = 0.0  # Default to low confidence
    #
    #     # Different strategies based on confidence level
    #     if conf_value < 0.3:
    #         # Very low confidence - ask for clarification
    #         responses = [
    #             "I'm not quite sure what you mean. Could you rephrase that?",
    #             "I want to make sure I understand correctly. Could you say that differently?",
    #             "I'm having trouble understanding. Could you provide more details?"
    #         ]
    #         import random
    #         response = random.choice(responses)
    #         action = 'clarify'
    #
    #     elif conf_value < 0.5:
    #         # Medium-low confidence - offer suggestions
    #         responses = [
    #             "I think you might be asking about: (1) Library hours, (2) Finding books, or (3) Borrowing policies. Which one interests you?",
    #             "Could this be about: Library hours, Book search, or Borrowing information?",
    #             "I can help with library hours, book searches, or borrowing questions. Which would you like?"
    #         ]
    #         import random
    #         response = random.choice(responses)
    #         action = 'suggest'
    #
    #     else:
    #         # Confidence is okay, but we still want to verify
    #         responses = [
    #             f"Just to make sure I understood: are you asking about '{user_message}'?",
    #             f"I think you're asking about: {user_message}. Is that correct?",
    #             f"Let me confirm: you want to know about '{user_message}', right?"
    #         ]
    #         import random
    #         response = random.choice(responses)
    #         action = 'confirm'
    #
    #     # Generate follow-up questions
    #     follow_ups = self._get_clarification_questions(user_message, conf_value)
    #
    #     return {
    #         'response': response,
    #         'action': action,
    #         'confidence': conf_value,
    #         'requires_clarification': True,
    #         'suggested_follow_ups': follow_ups,
    #         'original_message': user_message
    #     }

    def _get_clarification_questions(self, user_message: str, confidence) -> List[str]:
        """
        Generate clarification questions based on the user's message
        """
        # Ensure confidence is numeric
        try:
            conf_value = float(confidence)
        except (ValueError, TypeError):
            conf_value = 0.0

        questions = []

        # Common library topics to suggest
        library_topics = [
            "Library hours and schedule",
            "Finding and searching for books",
            "Borrowing and returning books",
            "Library policies and rules",
            "Research assistance",
            "Using library computers"
        ]

        # If confidence is very low, offer general topics
        if conf_value < 0.3:
            questions = library_topics[:3]

        # If we detect some keywords, offer related topics
        user_lower = user_message.lower()

        if any(word in user_lower for word in ['hour', 'time', 'open', 'close']):
            questions = ["Library opening hours", "Weekend hours", "Holiday schedule"]
        elif any(word in user_lower for word in ['book', 'find', 'search', 'look']):
            questions = ["Search by title", "Search by author", "E-book availability"]
        elif any(word in user_lower for word in ['borrow', 'loan', 'return', 'due']):
            questions = ["Borrowing period", "Late fees", "Renewing books"]
        else:
            # Default suggestions
            questions = ["Library hours", "Book search", "Borrowing information"]

        return questions

    def _determine_state(self, user_id: str, session_id: str, intent: str, confidence: float,
                         context: Dict = None) -> str:
        """
        Determine the current conversation state based on intent and context

        Returns:
            State string: 'greeting', 'searching', 'clarifying', 'confirming', 'completed', etc.
        """
        if context is None:
            context = {}

        # Get conversation history for this session
        history_key = f"{user_id}_{session_id}"
        conversation_history = context.get('history', [])

        # If this is first message, it's likely greeting
        if len(conversation_history) == 0:
            return 'greeting'

        # Check confidence level
        if confidence < 0.3:
            return 'clarifying'
        elif confidence < 0.6:
            return 'confirming'

        # Determine state based on intent
        intent_state_map = {
            'greeting': 'greeting',
            'farewell': 'farewell',
            'book_search': 'searching',
            'library_hours': 'informing',
            'borrowing_info': 'explaining',
            'research_help': 'assisting',
            'unknown': 'clarifying'
        }

        # Check if we're in a multi-turn conversation
        last_intent = None
        if conversation_history:
            last_intent = conversation_history[-1].get('intent')

        # If same intent repeated, might need clarification
        if last_intent == intent:
            return 'clarifying'

        # Get state from map or default
        return intent_state_map.get(intent, 'conversing')

    def _log_interaction(self, user_id: str, session_id: str, message: str,
                         response: str, intent: str, confidence: float,
                         processing_method: str, context: Dict = None):
        """
        Log user interaction for analytics and conversation tracking
        """
        if context is None:
            context = {}

        import time
        import json

        log_entry = {
            'timestamp': time.time(),
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'session_id': session_id,
            'user_message': message,
            'bot_response': response,
            'intent': intent,
            'confidence': float(confidence),
            'processing_method': processing_method,
            'context': context
        }

        # Print to console for debugging
        print(f"\n📝 INTERACTION LOG:")
        print(f"  User: {user_id}")
        print(f"  Session: {session_id}")
        print(f"  Message: '{message}'")
        print(f"  Response: '{response}'")
        print(f"  Intent: {intent} (confidence: {confidence:.2f})")
        print(f"  Method: {processing_method}")

        # You could also save to database or file here
        # Example: Save to JSON file
        try:
            log_file = 'chat_logs.json'
            logs = []

            # Try to read existing logs
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            # Add new log
            logs.append(log_entry)

            # Save back to file (limit to last 1000 entries)
            with open(log_file, 'w') as f:
                json.dump(logs[-1000:], f, indent=2, default=str)

        except Exception as e:
            print(f"⚠️ Failed to save log: {e}")

        # Update conversation history in context
        if 'conversation_history' not in context:
            context['conversation_history'] = []

        context['conversation_history'].append({
            'role': 'user',
            'message': message,
            'timestamp': log_entry['timestamp']
        })

        context['conversation_history'].append({
            'role': 'bot',
            'message': response,
            'intent': intent,
            'timestamp': log_entry['timestamp']
        })

        # Keep only last 20 messages to prevent memory issues
        if len(context['conversation_history']) > 20:
            context['conversation_history'] = context['conversation_history'][-20:]

        return context

    def _suggest_follow_ups(self, intent: str, confidence: float,
                            current_state: str, context: Dict = None) -> List[str]:
        """
        Generate relevant follow-up questions based on the conversation
        """
        if context is None:
            context = {}

        # Get conversation history
        history = context.get('conversation_history', [])

        # Base follow-ups by intent
        intent_follow_ups = {
            'greeting': [
                "What are the library hours?",
                "How do I search for books?",
                "What are the borrowing policies?",
                "Can you help with research?"
            ],
            'library_hours': [
                "What are weekend hours?",
                "Are you open on holidays?",
                "When is the library busiest?",
                "Do you have extended exam hours?"
            ],
            'book_search': [
                "How do I search by author?",
                "Can I search for e-books?",
                "How do I reserve a book?",
                "What if the book is checked out?"
            ],
            'borrowing_info': [
                "How long can I borrow books?",
                "What are the late fees?",
                "How do I renew a book?",
                "Can I borrow reference books?"
            ],
            'research_help': [
                "How do I access journals?",
                "Can you help with citations?",
                "Are there research guides?",
                "How do I use databases?"
            ],
            'unknown': [
                "Tell me about library hours",
                "How do I find a book?",
                "What are the borrowing rules?",
                "Can you help with research?"
            ]
        }

        # Get base suggestions
        suggestions = intent_follow_ups.get(intent, intent_follow_ups['unknown'])

        # Adjust based on confidence
        if confidence < 0.4:
            # Low confidence - offer broader options
            suggestions = [
                "Library hours information",
                "Book search help",
                "Borrowing policies",
                "Research assistance"
            ]
        elif confidence > 0.8:
            # High confidence - offer more specific follow-ups
            if intent == 'book_search':
                suggestions = [
                    "Search for fiction books",
                    "Find textbooks for my course",
                    "Look up books by a specific author",
                    "Check if a book is available"
                ]
            elif intent == 'library_hours':
                suggestions = [
                    "Today's opening hours",
                    "Weekend schedule",
                    "Special holiday hours",
                    "Quiet study hours"
                ]

        # Adjust based on conversation state
        if current_state == 'clarifying':
            suggestions = ["Could you rephrase?", "What specifically are you asking?",
                           "Let me try to understand better..."]
        elif current_state == 'confirming':
            suggestions = ["Yes, that's correct", "No, let me clarify", "Partly, but also..."]

        # Limit to 3-4 suggestions
        import random
        if len(suggestions) > 4:
            suggestions = random.sample(suggestions, 4)

        return suggestions

import json, os
from typing import Dict, Optional


class ResponseGenerator:
    def __init__(self, templates_file: str = 'app/data/response_templates.json'):
        print(f"📝 Loading response templates from: {templates_file}")

        # Multiple fallback locations
        possible_files = [
            templates_file,
            'app/data/response_templates.json',
            'app/data/templates.json'
        ]

        self.templates = {}
        loaded = False

        for file_path in possible_files:
            if os.path.exists(file_path):
                try:
                    # Try multiple encodings
                    content = self._read_file_with_encoding(file_path)
                    if content:
                        # Clean the content before parsing JSON
                        content = self._clean_unicode_content(content)
                        self.templates = json.loads(content)
                        print(f"✅ Loaded templates from: {file_path}")

                        # Debug: Check what was loaded
                        print(f"DEBUG: Available templates: {list(self.templates.keys())}")
                        if 'library_hours' in self.templates:
                            print(
                                f"DEBUG: library_hours template: {self.templates['library_hours'].get('main', '')[:100]}...")

                        loaded = True
                        break
                except Exception as e:
                    print(f"⚠️ Failed to load {file_path}: {e}")
                    continue

        if not loaded:
            print("⚠️ Could not load template files, using defaults")
            self.templates = self._get_default_templates()

    # def __init__(self, templates_file: str = 'app/data/response_templates.json'):
    #     print(f"📝 Loading response templates from: {templates_file}")
    #
    #     # Multiple fallback locations
    #     possible_files = [
    #         templates_file,
    #         'app/data/response_templates.json',
    #         'app/data/templates.json'
    #     ]
    #
    #     self.templates = {}
    #     loaded = False
    #
    #     for file_path in possible_files:
    #         if os.path.exists(file_path):
    #             try:
    #                 # Try multiple encodings
    #                 content = self._read_file_with_encoding(file_path)
    #                 if content:
    #                     self.templates = json.loads(content)
    #                     print(f"✅ Loaded templates from: {file_path}")
    #                     loaded = True
    #                     break
    #             except Exception as e:
    #                 print(f"⚠️ Failed to load {file_path}: {e}")
    #                 continue
    #
    #     if not loaded:
    #         print("⚠️ Could not load template files, using defaults")
    #         self.templates = self._get_default_templates()


    def _clean_unicode_content(self, content: str) -> str:
        """Clean Unicode content of common encoding issues"""
        if not content:
            return content

        # Common UTF-8 mis-encodings
        replacements = {
            'â€¢': '•',  # Bullet point
            'â€"': '—',  # Em dash
            'â€"': '–',  # En dash
            'â€™': "'",  # Right single quote
            'â€˜': "'",  # Left single quote
            'â€œ': '"',  # Left double quote
            'â€': '"',  # Right double quote
            'Ã©': 'é',  # é
            'Ã¨': 'è',  # è
            'Ã¢': 'â',  # â
            'Ã': 'à',  # à
            'Ã±': 'ñ',  # ñ
            'Ã³': 'ó',  # ó
            'Ãº': 'ú',  # ú
            'Ã': 'í',  # í
            'Ã¶': 'ö',  # ö
            'Ã¼': 'ü',  # ü
            'ÃŸ': 'ß',  # ß
            'Ã¦': 'æ',  # æ
            'Ã¸': 'ø',  # ø
            'Ã¥': 'å',  # å
        }

        # Apply replacements
        for bad, good in replacements.items():
            content = content.replace(bad, good)

        # Fix common emoji issues
        emoji_fixes = {
            '\ud83d\udcd6': '📚',  # Book emoji
            '\ud83d\udc4b': '👋',  # Waving hand
        }

        for bad, good in emoji_fixes.items():
            content = content.replace(bad, good)

        return content

    def _read_file_with_encoding(self, filepath: str) -> Optional[str]:
        """Read file trying multiple encodings"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        # Last resort: read as binary and clean
        try:
            with open(filepath, 'rb') as f:
                content = f.read()

            # Remove invalid UTF-8 bytes
            clean_bytes = bytes([b for b in content if b < 0x80 or b >= 0xA0])
            return clean_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"❌ All encoding attempts failed for {filepath}: {e}")
            return None

    def _get_default_templates(self) -> Dict:
        """Get default templates"""
        return {
            "greeting": {
                "main": "👋 **Hello! I'm the Babcock University Library Assistant.**\n\nI can help you with library services. How can I assist you today?",
                "follow_up": "Try asking about library hours or borrowing books."
            },
            "book_search": {
                "main": "I found {count} books matching your search.",
                "no_results": "No books found matching '{query}'.",
                "follow_up": "Try different keywords."
            },
            "library_hours": {
                "main": "📚 **Library Hours**\n\nWeekdays: 8:00 AM - 10:00 PM\nWeekends: 10:00 AM - 8:00 PM",
                "follow_up": ""
            },
            "fallback": {
                "main": "I'm here to help with library services.",
                "follow_up": "You can ask about library hours, borrowing, or finding resources."
            }
        }

    def generate(self, response_data: Dict, context: Dict, method: str) -> str:
        """Generate contextual response"""
        try:
            print(f"📝 Generating response with method: {method}")

            if method == 'rule_based':
                response = self._generate_from_rule(response_data, context)
            elif method == 'nlp_based':
                response = self._generate_from_nlp(response_data, context)
            elif method == 'knowledge_base':
                response = self._generate_from_kb(response_data, context)
            else:
                response = self._generate_clarification(response_data, context)

            # Clean the response before returning
            response = self._clean_response(response)
            print(f"✅ Generated response (cleaned): {response[:100]}...")
            return response

        except Exception as e:
            print(f"❌ Error in generate method: {e}")
            import traceback
            traceback.print_exc()

            # Return a safe, clean response
            return "I'm here to help with library services. How can I assist you today?"

    def _generate_from_kb(self, kb_data: Dict, context: Dict) -> str:
        """Generate response from knowledge base data"""
        try:
            # Extract knowledge base information
            answer = kb_data.get('answer', '')
            confidence = kb_data.get('confidence', 0)
            source = kb_data.get('source', '')

            # If we have a direct answer with good confidence
            if answer and confidence > 0.7:
                response = f"{answer}"

                # Add source attribution if available
                if source:
                    response += f"\n\n_This information comes from: {source}_"

                # Add follow-up if available
                follow_up = kb_data.get('follow_up', '')
                if follow_up:
                    response += f"\n\n{follow_up}"

                return response

            # If confidence is low, be more cautious
            elif answer and confidence > 0.5:
                return f"Based on available information: {answer}\n\n_I'm not entirely certain about this. You may want to verify with library staff._"

            # No answer found
            else:
                # Check if we have related topics
                related = kb_data.get('related_topics', [])
                if related:
                    topics = ", ".join(related[:3])
                    return f"I couldn't find a specific answer to your question.\n\n**Related topics you might find helpful:** {topics}\n\nWould you like me to search for any of these instead?"

                # Generic fallback
                return "I don't have specific information about that in my knowledge base. You might want to:\n1. Contact the library help desk\n2. Check the library website\n3. Visit the information desk in person"

        except Exception as e:
            print(f"⚠️ Error generating KB response: {e}")
            return "I encountered an issue retrieving information from the knowledge base. Please try again or contact library staff."

    def _generate_from_rule(self, rule_data: Dict, context: Dict) -> str:
        """Generate response from rule match"""
        template = rule_data['response_data']['template']
        variables = rule_data['response_data'].get('variables', {})

        # Fill template variables
        response = template
        for key, value in variables.items():
            response = response.replace(f'{{{key}}}', str(value))

        # Add contextual information if available
        if context.get('user_name'):
            response = f"Hi {context['user_name']}, {response}"

        return response

    def _generate_from_nlp(self, nlp_data: Dict, context: Dict) -> str:
        """Generate response from NLP analysis"""
        intent = nlp_data['intent']

        # Get template for intent
        template = self.templates.get(intent, {}).get('main',
                                                      "I can help you with that. Based on your query about {topic}...")

        # Extract entities for personalization - SAFELY
        entities = nlp_data.get('entities', [])
        entity_dict = {}

        for e in entities:
            if isinstance(e, dict):
                # Handle different possible entity structures
                if 'label' in e and 'text' in e:
                    entity_dict[e['label']] = e['text']
                elif 'entity' in e and 'value' in e:
                    entity_dict[e['entity']] = e['value']
                elif 'type' in e and 'value' in e:
                    entity_dict[e['type']] = e['value']

        # Fill template ONLY if we have variables to fill
        try:
            if entity_dict:  # Only format if we have entities
                response = template.format(**entity_dict)
            else:
                response = template  # Use template as-is
        except KeyError as e:
            print(f"⚠️ Missing key in template: {e}")
            response = template  # Fallback to original template
        except Exception as e:
            print(f"⚠️ Error formatting template: {e}")
            response = template

        # Add follow-up suggestions
        if self.templates.get(intent, {}).get('follow_up'):
            follow_up = self.templates[intent]['follow_up']
            response += f" {follow_up}"

        return response

    # def _generate_from_nlp(self, nlp_data: Dict, context: Dict) -> str:
    #     """Generate response from NLP analysis"""
    #     intent = nlp_data['intent']
    #
    #     # Get template for intent
    #     template = self.templates.get(intent, {}).get('main',
    #                                                   "I can help you with that. Based on your query about {topic}...")
    #
    #     # Extract entities for personalization
    #     entities = nlp_data.get('entities', [])
    #     entity_dict = {e['label']: e['text'] for e in entities}
    #
    #     # Fill template
    #     response = template.format(**entity_dict)
    #
    #     # Add follow-up suggestions
    #     if self.templates.get(intent, {}).get('follow_up'):
    #         follow_up = self.templates[intent]['follow_up']
    #         response += f" {follow_up}"
    #
    #     return response

    def _generate_clarification(self, data: Dict, context: Dict) -> str:
        """Generate clarification question"""
        unclear_entities = data.get('unclear_entities', [])

        if unclear_entities:
            entity_list = ", ".join(unclear_entities[:3])
            return f"I want to help you better. Could you clarify what you mean by {entity_list}?"

        # General clarification
        clarification_templates = [
            "Could you provide more details about what you're looking for?",
            "I'm not sure I understand. Could you rephrase your question?",
            "Are you looking for a specific book, library policy, or research help?"
        ]

        import random
        return random.choice(clarification_templates)

    def _fill_template(self, template: str, data: Dict) -> str:
        """Fill template variables with data"""
        if not template:
            return ""

        # Simple variable replacement
        for key, value in data.items():
            if isinstance(value, str):
                template = template.replace(f'{{{key}}}', value)

        return template

    def get_template(self, intent: str, part: str = 'main') -> str:
        """Get a specific template part"""
        return self.templates.get(intent, {}).get(part, '')

    # def _clean_response(self, text: str) -> str:
    #     """Clean response text of any encoding issues"""
    #     if not text:
    #         return ""
    #
    #     # Fix common encoding artifacts
    #     text = self._clean_unicode_content(text)
    #
    #     # Ensure it's valid UTF-8
    #     try:
    #         # Encode and decode to ensure valid UTF-8
    #         text = text.encode('utf-8', errors='replace').decode('utf-8')
    #     except:
    #         # If that fails, remove non-ASCII
    #         text = ''.join(char for char in text if ord(char) < 128)
    #
    #     return text

    def _clean_response(self, text: str) -> str:
        """Clean response text of encoding issues - IMPROVED VERSION"""
        if not text:
            return ""

        text = self._clean_unicode_content(text)

        # Direct replacements for your specific issues
        fixes = {
            'ð': '📚',  # Book emoji
            'â¢': '•',  # Bullet point
            'â€¢': '•',  # Another bullet variant
            'ð©': '👋',  # Waving hand (if present)
            'ð¬': '📖',  # Book (if present)
            'â': '-',  # Dash (if present)
        }

        # Apply fixes
        for bad, good in fixes.items():
            text = text.replace(bad, good)

        # Also clean any other mojibake (UTF-8 misinterpreted as Latin-1)
        common_mojibake = {
            'â\x80\x99': "'",  # Right single quote
            'â\x80\x9c': '"',  # Left double quote
            'â\x80\x9d': '"',  # Right double quote
            'â\x80\x93': '–',  # En dash
            'â\x80\x94': '—',  # Em dash
            'â\x80\xa2': '•',  # Bullet
            'â\x80¦': '…',  # Ellipsis
        }

        for bad, good in common_mojibake.items():
            text = text.replace(bad, good)

        # Finally, ensure valid UTF-8
        try:
            return text.encode('utf-8', errors='ignore').decode('utf-8')
        except:
            # If all else fails, keep only ASCII
            return ''.join(char for char in text if ord(char) < 128)
#
# import json, os
# import re
# from typing import Dict, Optional
#
#
# class ResponseGenerator:
#     def __init__(self, templates_file: str = 'app/data/response_templates.json'):
#         print(f"📝 Loading response templates from: {templates_file}")
#
#         # Multiple fallback locations
#         possible_files = [
#             templates_file,
#             'app/data/response_templates.json',
#             'app/data/templates.json'
#         ]
#
#         self.templates = {}
#         loaded = False
#
#         for file_path in possible_files:
#             if os.path.exists(file_path):
#                 try:
#                     # Try multiple encodings
#                     content = self._read_file_with_encoding(file_path)
#                     if content:
#                         # Clean the content before parsing JSON
#                         content = self._clean_unicode_content(content)
#                         self.templates = json.loads(content)
#                         print(f"✅ Loaded templates from: {file_path}")
#
#                         # Debug: Check what was loaded
#                         print(f"DEBUG: Available templates: {list(self.templates.keys())}")
#                         if 'library_hours' in self.templates:
#                             print(
#                                 f"DEBUG: library_hours template: {self.templates['library_hours'].get('main', '')[:100]}...")
#
#                         loaded = True
#                         break
#                 except Exception as e:
#                     print(f"⚠️ Failed to load {file_path}: {e}")
#                     continue
#
#         if not loaded:
#             print("⚠️ Could not load template files, using defaults")
#             self.templates = self._get_default_templates()
#
#     def _clean_unicode_content(self, content: str) -> str:
#         """Clean Unicode content of common encoding issues"""
#         if not content:
#             return content
#
#         # Common UTF-8 mis-encodings
#         replacements = {
#             'â€¢': '•',  # Bullet point
#             'â€"': '—',  # Em dash
#             'â€"': '–',  # En dash
#             'â€™': "'",  # Right single quote
#             'â€˜': "'",  # Left single quote
#             'â€œ': '"',  # Left double quote
#             'â€': '"',  # Right double quote
#             'Ã©': 'é',  # é
#             'Ã¨': 'è',  # è
#             'Ã¢': 'â',  # â
#             'Ã': 'à',  # à
#             'Ã±': 'ñ',  # ñ
#             'Ã³': 'ó',  # ó
#             'Ãº': 'ú',  # ú
#             'Ã': 'í',  # í
#             'Ã¶': 'ö',  # ö
#             'Ã¼': 'ü',  # ü
#             'ÃŸ': 'ß',  # ß
#             'Ã¦': 'æ',  # æ
#             'Ã¸': 'ø',  # ø
#             'Ã¥': 'å',  # å
#         }
#
#         # Apply replacements
#         for bad, good in replacements.items():
#             content = content.replace(bad, good)
#
#         # Fix common emoji issues
#         emoji_fixes = {
#             '\ud83d\udcd6': '📚',  # Book emoji
#             '\ud83d\udc4b': '👋',  # Waving hand
#         }
#
#         for bad, good in emoji_fixes.items():
#             content = content.replace(bad, good)
#
#         return content
#
#     def _read_file_with_encoding(self, filepath: str) -> Optional[str]:
#         """Read file trying multiple encodings - IMPROVED"""
#         encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
#
#         for encoding in encodings:
#             try:
#                 with open(filepath, 'r', encoding=encoding) as f:
#                     content = f.read()
#
#                     # Debug: Check what we read
#                     if encoding == 'utf-8-sig' or encoding == 'utf-8':
#                         print(f"DEBUG: Read with {encoding}, first 200 chars: {content[:200]}")
#
#                     return content
#             except UnicodeDecodeError:
#                 continue
#
#         # If all else fails, read as binary and try to decode
#         try:
#             with open(filepath, 'rb') as f:
#                 raw_bytes = f.read()
#
#             # Try to detect encoding
#             import chardet
#             result = chardet.detect(raw_bytes)
#             detected_encoding = result['encoding']
#             confidence = result['confidence']
#
#             print(f"DEBUG: Detected encoding: {detected_encoding} (confidence: {confidence})")
#
#             if detected_encoding:
#                 try:
#                     return raw_bytes.decode(detected_encoding)
#                 except:
#                     pass
#
#             # Last resort: replace errors
#             return raw_bytes.decode('utf-8', errors='replace')
#         except Exception as e:
#             print(f"❌ All encoding attempts failed for {filepath}: {e}")
#             return None
#
#     def _get_default_templates(self) -> Dict:
#         """Get default templates with proper Unicode"""
#         return {
#             "greeting": {
#                 "main": "👋 **Hello! I'm the Babcock University Library Assistant.**\n\nI can help you with library services. How can I assist you today?",
#                 "follow_up": "Try asking about library hours or borrowing books."
#             },
#             "book_search": {
#                 "main": "I found {count} books matching your search.",
#                 "no_results": "No books found matching '{query}'.",
#                 "follow_up": "Try different keywords."
#             },
#             "library_hours": {
#                 "main": "📚 **Library Hours**\n\n**Weekdays (Mon-Fri):** 8:00 AM - 10:00 PM\n**Weekends (Sat-Sun):** 10:00 AM - 8:00 PM\n\n**Special Hours:**\n• Exam Period: 7:00 AM - 12:00 AM\n• Holidays: Closed\n\nCurrent time: {current_time} Would you like to know about specific services or holiday schedules?",
#                 "follow_up": ""
#             },
#             "fallback": {
#                 "main": "I'm here to help with library services.",
#                 "follow_up": "You can ask about library hours, borrowing, or finding resources."
#             }
#         }
#
#     def generate(self, response_data: Dict, context: Dict, method: str) -> str:
#         """Generate contextual response"""
#         try:
#             print(f"📝 Generating response with method: {method}")
#
#             if method == 'rule_based':
#                 response = self._generate_from_rule(response_data, context)
#             elif method == 'nlp_based':
#                 response = self._generate_from_nlp(response_data, context)
#             elif method == 'knowledge_base':
#                 response = self._generate_from_kb(response_data, context)
#             else:
#                 response = self._generate_clarification(response_data, context)
#
#             # Clean the response before returning
#             response = self._clean_response(response)
#             print(f"✅ Generated response (cleaned): {response[:100]}...")
#             return response
#
#         except Exception as e:
#             print(f"❌ Error in generate method: {e}")
#             import traceback
#             traceback.print_exc()
#
#             # Return a safe, clean response
#             return "I'm here to help with library services. How can I assist you today?"
#
#     def _clean_response(self, text: str) -> str:
#         """Clean response text of any encoding issues"""
#         if not text:
#             return ""
#
#         # Fix common encoding artifacts
#         text = self._clean_unicode_content(text)
#
#         # Ensure it's valid UTF-8
#         try:
#             # Encode and decode to ensure valid UTF-8
#             text = text.encode('utf-8', errors='replace').decode('utf-8')
#         except:
#             # If that fails, remove non-ASCII
#             text = ''.join(char for char in text if ord(char) < 128)
#
#         return text

    # ... rest of your methods remain the same ...
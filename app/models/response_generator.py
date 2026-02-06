import json, os
import re
from typing import Dict, Optional, List
from datetime import datetime


class ResponseGenerator:
    def __init__(self, templates_file: str = 'app/data/response_templates.json'):
        print(f"📝 Loading response templates from: {templates_file}")

        self.templates = self._get_default_templates()
        if os.path.exists(templates_file):
            try:
                content = self._read_file_with_encoding(templates_file)
                if content:
                    content = self._clean_unicode_content(content)
                    file_templates = json.loads(content)
                    self.templates.update(file_templates)
                    print(f"✅ Loaded templates from: {templates_file}")
            except Exception as e:
                print(f"⚠️ Failed to load {templates_file}: {e}")

    def _clean_unicode_content(self, content: str) -> str:
        """Clean Unicode content of common encoding issues"""
        if not content:
            return content
        replacements = {
            'â€¢': '•', 'â€"': '—', 'â€™': "'", 'â€˜': "'", 'â€œ': '"', 'â€': '"',
            'Ã©': 'é', 'Ã¨': 'è', 'Ã¢': 'â', 'Ã': 'à', 'Ã±': 'ñ', 'Ã³': 'ó',
            'Ãº': 'ú', 'Ã¶': 'ö', 'Ã¼': 'ü', 'ÃŸ': 'ß', 'Ã¦': 'æ', 'Ã¸': 'ø', 'Ã¥': 'å',
        }
        for bad, good in replacements.items():
            content = content.replace(bad, good)
        emoji_fixes = {'\ud83d\udcd6': '📚', '\ud83d\udc4b': '👋'}
        for bad, good in emoji_fixes.items():
            content = content.replace(bad, good)
        return content

    def _read_file_with_encoding(self, filepath: str) -> Optional[str]:
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None

    def _get_default_templates(self) -> Dict:
        return {
            "greeting": {
                "main": "👋 **Hello! I'm the Babcock University Library Assistant.** \n\nI can help you with:\n• 📚 Finding books and resources\n• 🕐 Library hours and policies  \n• 🔍 Research and database access\n• 📝 Citations and references\n• 📞 Contact information\n\n**How can I assist you today?** Try asking:\n'What are the library hours?'\n'Find books about computer science'\n'How do I renew a book?'\n'Help with my research paper'",
                "follow_up": ""
            },
            "book_search": {
                "main": "📚 **BOOKS FOUND ({count})**\n\n{book_list}",
                "no_results": "❌ That book isn't in our catalog. Would you like to:\n1. Try different search terms?\n2. Request an inter-library loan?\n3. Check eBook alternatives?",
                "follow_up": "Need help locating any of these?"
            },
            "library_hours": {
                "main": "🕐 **LIBRARY HOURS**\n\nWeekdays: **8:00 AM - 10:00 PM**\nWeekends: **10:00 AM - 8:00 PM**\n\n• Exam Period: 7:00 AM - 12:00 AM\n• Holidays: Closed\n\n_Current time: {current_time}_",
                "follow_up": "Would you like to know about holiday schedules?"
            },
            "borrowing_policy": {
                "main": "ℹ️ **BORROWING POLICY**\n\n**Students:**\n• Maximum books: **5**\n• Loan period: **14 days**\n• Renewals: **1 renewal** (if no holds)\n\n**Staff/Faculty:**\n• Maximum books: **10**\n• Loan period: **30 days**\n• Renewals: **2 renewals**\n\n**Overdue Fines:** ₦50 per day per book",
                "follow_up": "Need to know how to renew your books?"
            },
            "contact_info": {
                "main": "📞 **CONTACT INFORMATION**\n\n{contact_list}",
                "follow_up": "Is there a specific department you're trying to reach?"
            },
            "research_assistance": {
                "main": "🔍 **RESEARCH ASSISTANCE**\n\nI can help you find papers, databases, and guide you with citations.\n\n**Key Databases:**\n• JSTOR\n• IEEE Xplore\n• ScienceDirect\n\n**Tips:**\n• Use specific keywords\n• Check our citation guides for APA/MLA",
                "follow_up": "What is your research topic?"
            },
            "book_renewal": {
                "main": "📚 **BOOK RENEWAL**\n\nYou can renew books through your online account or at the circulation desk.\n\n**Policy:**\n• **1 renewal** for students\n• **2 renewals** for staff/faculty\n• Renewal is only possible if there are no active holds on the book.",
                "follow_up": "Would you like me to check your borrowed books?"
            },
            "book_reservation": {
                "main": "📚 **BOOK RESERVATION**\n\nIf a book is currently checked out, you can place a hold on it.\n\n**Steps:**\n1. Search for the book in our catalog\n2. Click 'Place Hold'\n3. You will be notified via email when it's available.",
                "follow_up": "Need help finding a specific book to reserve?"
            },
            "study_rooms": {
                "main": "🏫 **STUDY ROOMS**\n\nWe have private and group study rooms available for booking.\n\n• **Duration:** Max 3 hours per session\n• **Capacity:** 2-8 people per room\n• **Booking:** Available via the library website or at the information desk.",
                "follow_up": "Would you like the link to the booking system?"
            },
            "library_services": {
                "main": "ℹ️ **LIBRARY SERVICES**\n\nBeyond books, we offer several services to support your studies:\n\n• 🖨️ **Printing & Scanning:** Available on the 1st floor\n• 💻 **Computer Lab:** Access to research databases\n• 🎓 **Workshops:** Citation management and research strategies\n• ☕ **Study Café:** Open during regular hours",
                "follow_up": "Are you interested in any specific service?"
            },
            "fallback": {
                "main": "I'm not sure I understand. Could you rephrase? For example, you could ask:\n• 'What are the library hours?'\n• 'How do I renew a book?'\n• 'Find books about biology'",
                "follow_up": ""
            }
        }

    def generate(self, response_data: Dict, context: Dict, method: str) -> str:
        try:
            print(f"📝 Generating response with method: {method}")

            # Add time-based greeting if it's the start
            prefix = ""
            if response_data.get('intent') == 'greeting':
                hour = datetime.now().hour
                if hour < 12: prefix = "Good morning! "
                elif hour < 17: prefix = "Good afternoon! "
                else: prefix = "Good evening! "

            if method == 'rule_based':
                response = self._generate_from_rule(response_data, context)
            elif method == 'nlp_based':
                response = self._generate_from_nlp(response_data, context)
            elif method == 'knowledge_base':
                response = self._generate_from_kb(response_data, context)
            else:
                response = self._generate_clarification(response_data, context)

            response = prefix + self._clean_response(response)
            return response

        except Exception as e:
            import traceback
            traceback.print_exc()
            return "I'm here to help with library services. How can I assist you today?"

    def _generate_from_nlp(self, nlp_data: Dict, context: Dict) -> str:
        intent = nlp_data.get('intent', 'fallback')
        template_obj = self.templates.get(intent, self.templates.get('fallback', {}))

        # Check for database results first if relevant
        db_results = nlp_data.get('db_results')

        if intent == 'book_search':
            if db_results:
                book_strings = []
                for b in db_results:
                    book_strings.append(f"• **{b['title']}** by {b['author']}\n  📍 Location: {b['location']}\n  📅 Available: {b['copies_available']} copies")
                try:
                    return template_obj['main'].format(count=len(db_results), book_list="\n".join(book_strings))
                except KeyError:
                    return f"📚 **BOOKS FOUND ({len(db_results)})**\n\n" + "\n".join(book_strings)
            else:
                query = nlp_data.get('text', 'your query')
                try:
                    return template_obj['no_results'].format(query=query)
                except KeyError:
                    return "❌ That book isn't in our catalog. Would you like to:\n1. Try different search terms?\n2. Request an inter-library loan?\n3. Check eBook alternatives?"

        if intent == 'contact_info':
            if db_results:
                contact_strings = []
                for c in db_results:
                    contact_strings.append(f"• **{c['department']}**\n  📞 {c['phone']}\n  📧 {c['email']}\n  🕐 Hours: {c['hours']}")
                return template_obj['main'].format(contact_list="\n".join(contact_strings))

        template = template_obj.get('main', "I can help you with that.")
        entities = nlp_data.get('entities', [])
        entity_dict = {e['label']: e['text'] for e in entities if isinstance(e, dict) and 'label' in e}
        entity_dict['current_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            response = self._safe_format(template, entity_dict)
        except Exception:
            response = template

        follow_up = template_obj.get('follow_up')
        if follow_up:
            response += f"\n\n{follow_up}"

        return response

    def _safe_format(self, template: str, data: Dict) -> str:
        def replace(match):
            key = match.group(1)
            return str(data.get(key, match.group(0)))
        return re.sub(r'\{(\w+)\}', replace, template)

    def _clean_response(self, text: str) -> str:
        if not text: return ""
        text = self._clean_unicode_content(text)
        fixes = {'ð': '📚', 'â¢': '•', 'â€¢': '•'}
        for bad, good in fixes.items():
            text = text.replace(bad, good)
        try:
            return text.encode('utf-8', errors='ignore').decode('utf-8')
        except:
            return ''.join(char for char in text if ord(char) < 128)

    def _generate_from_rule(self, rule_data: Dict, context: Dict) -> str:
        # Simplistic rule generation for now
        return rule_data.get('response_data', {}).get('template', rule_data.get('response_template', "I understand."))

    def _generate_from_kb(self, kb_data: Dict, context: Dict) -> str:
        return kb_data.get('answer', "I searched our knowledge base but couldn't find a specific answer.")

    def _generate_clarification(self, data: Dict, context: Dict) -> str:
        return self.templates['fallback']['main']

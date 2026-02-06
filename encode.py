#!/usr/bin/env python3
"""
Fix JSON file encoding issues
"""

import json
import os




def fix_json_file(file_path):
    """Fix JSON file encoding"""
    try:
        # Read with multiple encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✅ Read {file_path} with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        else:
            # If all encodings fail, read as binary and decode
            with open(file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
            print(f"✅ Read {file_path} with utf-8 ignore errors")

        # Parse JSON
        data = json.loads(content)

        # Write back with UTF-8
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Fixed {file_path} encoding")
        return True

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False


def create_simple_rules():
    """Create simple rules file"""
    simple_rules = {
  "rules": [
    {
      "id": "rule_001",
      "pattern": "(?i)(library|opening|close|hours?|schedule)",
      "response": "The library is open from 8:00 AM to 10:00 PM on weekdays (Monday-Friday), and from 10:00 AM to 8:00 PM on weekends (Saturday-Sunday).",
      "priority": 1,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_002",
      "pattern": "(?i)(borrow|loan|check\\s*out|take\\s*out)",
      "response": "Students can borrow up to 5 books for 14 days. Staff members can borrow up to 10 books for 30 days. You can renew books once if no one has placed a hold on them.",
      "priority": 1,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_003",
      "pattern": "(?i)(return|due|late|fine|overdue)",
      "response": "Books are due on the date stamped on your receipt. Overdue fines are ₦50 per day per book. You can return books at the circulation desk or in the book drop outside the library.",
      "priority": 1,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_004",
      "pattern": "(?i)(contact|phone|email|address|location)",
      "response": "You can contact the library at:\n📞 Phone: 123-456-7890\n📧 Email: library@babcock.edu.ng\n📍 Address: Babcock University Library, Ilishan-Remo, Ogun State\n🕒 Visit during opening hours",
      "priority": 1,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_005",
      "pattern": "(?i)(wifi|internet|wireless|connection)",
      "response": "Connect to 'Babcock-Library' WiFi network. Use your student ID as both username and password. For technical issues, contact the IT help desk.",
      "priority": 2,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_006",
      "pattern": "(?i)(print|printing|printer|photocopy)",
      "response": "Printing and photocopying services are available at the Digital Resource Center on the ground floor. Cost is ₦10 per page for black/white and ₦50 per page for color. Payment can be made with your student ID card.",
      "priority": 2,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_007",
      "pattern": "(?i)(quiet|silent|study\\s*area|noise)",
      "response": "The library has designated quiet study areas on floors 2 and 3. Group study rooms are available on the ground floor and can be booked at the circulation desk. Please maintain silence in quiet zones.",
      "priority": 2,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_008",
      "pattern": "(?i)(database|journal|article|research)",
      "response": "The library provides access to several online databases including JSTOR, IEEE Xplore, ScienceDirect, and SpringerLink. You can access them from any campus computer or through the library website using your student credentials.",
      "priority": 2,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_009",
      "pattern": "(?i)(hello|hi|hey|greetings|good\\s*(morning|afternoon|evening))",
      "response": "Hello! 👋 I'm the Babcock University Library Assistant. How can I help you today?",
      "priority": 3,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_010",
      "pattern": "(?i)(thank|thanks|appreciate|grateful)",
      "response": "You're welcome! 😊 Is there anything else I can help you with?",
      "priority": 3,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_011",
      "pattern": "(?i)(bye|goodbye|see\\s*you|farewell)",
      "response": "Goodbye! 👋 Feel free to come back if you need more assistance with the library.",
      "priority": 3,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_012",
      "pattern": "(?i)(membership|register|sign\\s*up|library\\s*card)",
      "response": "All Babcock University students and staff are automatically library members. Your student/staff ID serves as your library card. Please bring it with you when visiting the library.",
      "priority": 2,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_013",
      "pattern": "(?i)(reserve|hold|book\\s*a\\s*book|request)",
      "response": "You can place a hold on books that are currently checked out. Visit the circulation desk or use the online catalog. You'll be notified when the book is available.",
      "priority": 2,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_014",
      "pattern": "(?i)(find|locate|where\\s*is|shelf|location\\s*of)",
      "response": "Books are organized using the Library of Congress classification system. You can search for a book in the online catalog to get its call number and location. Library staff can also help you locate books.",
      "priority": 2,
      "requires_context": False,
      "conditions": []
    },
    {
      "id": "rule_015",
      "pattern": "(?i)(librarian|staff|help\\s*desk|assistance)",
      "response": "Library staff are available at the circulation and reference desks during opening hours. For specialized research help, you can book an appointment with a subject librarian.",
      "priority": 2,
      "requires_context": False,
      "conditions": []
    }
  ]
}

    return simple_rules


def main():
    print("🔧 Fixing JSON encoding issues...")

    # List of files to fix/create
    files = [
        ('app/data/rules.json', create_simple_rules()),
        ('app/data/response_templates.json', {
  "book_search": {
    "main": "I found {count} book(s) matching your search:\n\n{book_list}\n\nWould you like more details about any of these books?",
    "no_results": "I couldn't find any books matching '{query}'. Try using different keywords or check the spelling.",
    "follow_up": "You can ask me about a specific book's availability, location, or details.",
    "single_result": "I found this book:\n📚 **{title}**\n👤 Author: {author}\n📅 Year: {year}\n🔢 Call Number: {call_number}\n📍 Location: {location}\n✅ Status: {status}"
  },
  "library_hours": {
    "main": "📚 **Library Hours**\n\n**Weekdays (Mon-Fri):** 8:00 AM - 10:00 PM\n**Weekends (Sat-Sun):** 10:00 AM - 8:00 PM\n\n**Special Hours:**\n• Exam Period: 7:00 AM - 12:00 AM\n• Holidays: Closed\n\nCurrent time: {current_time}",
    "follow_up": "Would you like to know about specific services or holiday schedules?"
  },
  "borrowing_info": {
    "main": "📖 **Borrowing Policy**\n\n**Students:**\n• Maximum books: 5\n• Loan period: 14 days\n• Renewals: 1 renewal (if no holds)\n\n**Staff:**\n• Maximum books: 10\n• Loan period: 30 days\n• Renewals: 2 renewals\n\n**Overdue Fines:** ₦50 per day per book",
    "follow_up": "Need to know how to renew or check your due dates?"
  },
  "policy_query": {
    "main": "Here's our library policy regarding {topic}:\n\n{policy_details}\n\nFor the complete policy document, visit the library website or ask at the circulation desk.",
    "follow_up": "Is there a specific aspect of the policy you'd like clarified?"
  },
  "research_help": {
    "main": "I can help you with research! Here are some resources:\n\n**Databases Available:**\n• JSTOR (Arts & Sciences)\n• IEEE Xplore (Engineering)\n• ScienceDirect (Science)\n• SpringerLink (All disciplines)\n• PubMed (Medicine)\n\n**Research Guides:** Available for each department on the library website.",
    "follow_up": "Would you like help with a specific database or finding articles on a topic?"
  },
  "citation_help": {
    "main": "**Citation Styles Support**\n\nThe library provides help with:\n• APA 7th Edition\n• MLA 9th Edition\n• Chicago 17th Edition\n• IEEE\n\n**Resources:**\n• Citation guides at reference desk\n• Online citation generators on library website\n• Zotero/Mendeley workshops\n\nExample {style} citation for a book:\n{example}",
    "follow_up": "Need help with a specific citation or formatting question?"
  },
  "general_info": {
    "main": "I understand you're asking about {topic}. Here's what I can tell you:\n\n{information}\n\nIs this what you were looking for?",
    "follow_up": "Would you like more details or information on a related topic?"
  },
  "clarification": {
    "main": "I want to make sure I understand correctly. Are you asking about {topic1} or {topic2}?",
    "follow_up": "Please rephrase your question or provide more details."
  },
  "fallback": {
    "main": "I'm not sure I fully understand your question about {topic}. Could you provide more details or rephrase it?",
    "follow_up": "I can help you with:\n• Finding books and articles\n• Library hours and policies\n• Borrowing and returning items\n• Research and citation help\n• Library services and facilities"
  },
  "greeting": {
    "main": "👋 **Hello! I'm the Babcock University Library Assistant.**\n\nI can help you with:\n• 📚 Finding books and resources\n• 🕒 Library hours and policies\n• 🔍 Research and database access\n• 📝 Citation and reference help\n• 💬 General library information\n\n**How can I assist you today?**",
    "follow_up": "Try asking me something like:\n\"What are the library hours?\"\n\"How do I borrow a book?\"\n\"Find books about computer science\""
  },
  "error": {
    "main": "I apologize, but I encountered an error while processing your request. Please try again or contact library staff for assistance.",
    "follow_up": "You can try rephrasing your question or ask about a different topic."
  }
}),
        ('app/data/knowledge_base.json', {
  "entries": [
    {
      "id": "kb_001",
      "category": "Library Hours",
      "questions": [
        "When is the library open?",
        "What are your hours?",
        "Are you open now?",
        "Library opening times",
        "Closing time"
      ],
      "answer": "The library is open:\n\n**Regular Hours:**\n• Monday-Friday: 8:00 AM - 10:00 PM\n• Saturday-Sunday: 10:00 AM - 8:00 PM\n\n**Extended Hours (During Exams):**\n• Monday-Sunday: 7:00 AM - 12:00 AM\n\n**Holiday Schedule:**\nThe library is closed on official university holidays.",
      "metadata": {
        "last_updated": "2024-01-15",
        "source": "Library Policy",
        "priority": 1
      }
    },
    {
      "id": "kb_002",
      "category": "Borrowing Policy",
      "questions": [
        "How many books can I borrow?",
        "What is the loan period?",
        "Can I renew books?",
        "Borrowing limits",
        "Loan duration"
      ],
      "answer": "**Borrowing Limits:**\n\n**For Students:**\n• Maximum books: 5\n• Loan period: 14 days\n• Renewals allowed: 1 time (if no holds)\n\n**For Staff:**\n• Maximum books: 10\n• Loan period: 30 days\n• Renewals allowed: 2 times\n\n**Overdue Items:**\n• Fine: ₦50 per day per book\n• Maximum fine: ₦1000 per book\n• Borrowing privileges suspended until fines paid",
      "metadata": {
        "last_updated": "2024-01-15",
        "source": "Circulation Policy",
        "priority": 1
      }
    },
    {
      "id": "kb_003",
      "category": "Library Services",
      "questions": [
        "What services does the library offer?",
        "Can I print in the library?",
        "Is there WiFi?",
        "Study rooms",
        "Research help"
      ],
      "answer": "**Library Services:**\n\n1. **Borrowing Services** - Books, journals, media\n2. **Research Assistance** - Librarian consultations\n3. **Printing & Copying** - B&W (₦10/page), Color (₦50/page)\n4. **WiFi Access** - 'Babcock-Library' network\n5. **Study Spaces** - Quiet zones, group study rooms\n6. **Computer Lab** - 50+ computers with internet\n7. **Database Access** - 50+ academic databases\n8. **Interlibrary Loan** - Request materials from other libraries\n9. **Reference Desk** - Research and citation help\n10. **Workshops** - Regular training sessions",
      "metadata": {
        "last_updated": "2024-01-15",
        "source": "Services Brochure",
        "priority": 2
      }
    },
    {
      "id": "kb_004",
      "category": "Finding Books",
      "questions": [
        "How do I find a book?",
        "Search the catalog",
        "Locate books on shelf",
        "Call numbers",
        "Book locations"
      ],
      "answer": "**Finding Books in the Library:**\n\n1. **Search Online Catalog:**\n   • Visit library website\n   • Use search box\n   • Filter by author, title, subject\n\n2. **Understand Call Numbers:**\n   • Books organized by Library of Congress system\n   • Example: QA76.73.P98 (Computer Science section)\n\n3. **Locate in Library:**\n   • Ground Floor: Reference, New Arrivals\n   • 1st Floor: Social Sciences, Humanities\n   • 2nd Floor: Sciences, Engineering\n   • 3rd Floor: Quiet Study, Special Collections\n\n4. **Get Help:**\n   • Ask at circulation desk\n   • Use library floor maps\n   • Request librarian assistance",
      "metadata": {
        "last_updated": "2024-01-15",
        "source": "Library Guide",
        "priority": 2
      }
    },
    {
      "id": "kb_005",
      "category": "Digital Resources",
      "questions": [
        "Online databases",
        "E-books access",
        "Journal articles",
        "Remote access",
        "Electronic resources"
      ],
      "answer": "**Digital Resources Available:**\n\n**Databases (On-campus):**\n• JSTOR - Arts & Sciences\n• IEEE Xplore - Engineering\n• ScienceDirect - Science\n• SpringerLink - Multidisciplinary\n• PubMed - Medicine\n• ACM Digital Library - Computing\n• ProQuest - Dissertations & Theses\n\n**E-Book Collections:**\n• EBSCO eBooks\n• Springer eBooks\n• O'Reilly Learning\n\n**Remote Access:**\nUse your Babcock University credentials to access all digital resources from anywhere.\n\n**Research Guides:**\nSubject-specific guides available on library website.",
      "metadata": {
        "last_updated": "2024-01-15",
        "source": "Digital Resources",
        "priority": 2
      }
    },
    {
      "id": "kb_006",
      "category": "Library Facilities",
      "questions": [
        "Study areas",
        "Computer lab",
        "Group study rooms",
        "Printing facilities",
        "Library layout"
      ],
      "answer": "**Library Facilities:**\n\n**Ground Floor:**\n• Circulation Desk\n• Reference Collection\n• New Arrivals\n• Group Study Rooms (Bookable)\n• Computer Lab (50+ PCs)\n• Printing/Copying Station\n\n**First Floor:**\n• Social Sciences Collection\n• Humanities Collection\n• Quiet Study Area\n• Current Periodicals\n\n**Second Floor:**\n• Sciences Collection\n• Engineering Collection\n• Quiet Study Carrels\n• Thesis Collection\n\n**Third Floor:**\n• Special Collections\n• Archives\n• Silent Study Zone\n• Faculty Research Area\n\n**Other Facilities:**\n• WiFi throughout building\n• Drinking water stations\n• Restrooms on each floor\n• Elevator access\n• Wheelchair accessible",
      "metadata": {
        "last_updated": "2024-01-15",
        "source": "Facility Guide",
        "priority": 3
      }
    },
    {
      "id": "kb_007",
      "category": "Membership",
      "questions": [
        "Who can use the library?",
        "Library membership",
        "Alumni access",
        "Visitor policy",
        "Library card"
      ],
      "answer": "**Library Membership:**\n\n**Primary Users (Automatic Membership):**\n• All Babcock University students\n• All Babcock University staff\n• Use your university ID as library card\n\n**Secondary Users (With Conditions):**\n• Alumni: Free access with alumni card\n• Visiting scholars: Letter from department required\n• Consortium members: Reciprocal agreement\n\n**Guest Users:**\n• Limited access to physical collection\n• No borrowing privileges\n• Internet access: ₦500/day\n\n**All users must:**\n• Register at circulation desk\n• Follow library rules and regulations\n• Respect quiet study areas",
      "metadata": {
        "last_updated": "2024-01-15",
        "source": "Membership Policy",
        "priority": 3
      }
    },
    {
      "id": "kb_008",
      "category": "Research Help",
      "questions": [
        "How to do research?",
        "Literature review",
        "Finding articles",
        "Citation help",
        "Research consultation"
      ],
      "answer": "**Getting Research Help:**\n\n1. **Research Consultations:**\n   • Book appointment with subject librarian\n   • 30-60 minute sessions\n   • Help with search strategies, databases, citations\n\n2. **Research Guides:**\n   • Subject-specific guides on library website\n   • Database recommendations\n   • Citation style guides\n\n3. **Workshops:**\n   • Database training sessions\n   • Citation management (Zotero/Mendeley)\n   • Research skills development\n\n4. **Online Help:**\n   • Live chat with librarian\n   • Email research questions\n   • Video tutorials on website\n\n5. **Citation Help:**\n   • Style guides at reference desk\n   • Online citation generators\n   • Individual consultation available",
      "metadata": {
        "last_updated": "2024-01-15",
        "source": "Research Services",
        "priority": 2
      }
    },
    {
      "id": "kb_009",
      "category": "Library Rules",
      "questions": [
        "Library policies",
        "Code of conduct",
        "Food and drink",
        "Noise policy",
        "Cell phone use"
      ],
      "answer": "**Library Rules & Conduct:**\n\n**General Conduct:**\n• Respect quiet study areas\n• Keep conversations at low volume\n• Use cell phones in designated areas only\n• No disruptive behavior\n\n**Food & Drink:**\n• Covered drinks allowed\n• Snacks allowed in cafeteria only\n• No hot meals in study areas\n• Clean up after yourself\n\n**Resource Use:**\n• Handle library materials carefully\n• Return books on time\n• Report damaged items\n• No marking in books\n\n**Computer Use:**\n• Academic purposes priority\n• No inappropriate websites\n• Save files to personal devices\n• Log out when finished\n\n**Violations may result in:**\n• Warning\n• Temporary suspension\n• Loss of privileges\n• Disciplinary action",
      "metadata": {
        "last_updated": "2024-01-15",
        "source": "Conduct Policy",
        "priority": 3
      }
    },
    {
      "id": "kb_010",
      "category": "Contact Information",
      "questions": [
        "How to contact library?",
        "Library phone number",
        "Email address",
        "Staff directory",
        "Location address"
      ],
      "answer": "**Contact the Library:**\n\n**Main Library:**\n📍 Address: Babcock University Library\n           Ilishan-Remo, Ogun State\n           Nigeria\n📞 Phone: +234 (0)123 456 7890\n📧 Email: library@babcock.edu.ng\n🌐 Website: library.babcock.edu.ng\n\n**Department Contacts:**\n• Circulation Desk: Ext. 1001\n• Reference Desk: Ext. 1002\n• Technical Services: Ext. 1003\n• Digital Resources: Ext. 1004\n• Interlibrary Loan: Ext. 1005\n\n**Social Media:**\n• Twitter: @BabcockLibrary\n• Facebook: Babcock University Library\n• Instagram: @babcocklibrary\n\n**Office Hours:**\nMonday-Friday: 8:00 AM - 5:00 PM",
      "metadata": {
        "last_updated": "2024-01-15",
        "source": "Contact Info",
        "priority": 1
      }
    }
  ]
}),
        ('app/data/intent_examples.json', {
  "book_search": [
    "Find books about computer science",
    "Search for Python programming books",
    "I need books on artificial intelligence",
    "Look for novels by Chinua Achebe",
    "Find resources for my research paper",
    "Search the catalog for engineering textbooks",
    "Where can I find physics books?",
    "Books about Nigerian history"
  ],
  "borrowing_info": [
    "How many books can I borrow?",
    "What is the loan period?",
    "Can I renew my books?",
    "How do I return books?",
    "What are the overdue fines?",
    "Borrowing policy for students",
    "How long can I keep a book?",
    "Renewal process"
  ],
  "library_hours": [
    "When is the library open?",
    "What are your hours today?",
    "Are you open on weekends?",
    "Closing time for the library",
    "Library schedule for holidays",
    "What time do you open?",
    "Extended hours during exams",
    "Is the library open now?"
  ],
  "policy_query": [
    "What is the food policy?",
    "Can I bring my laptop?",
    "Is there a dress code?",
    "Library rules and regulations",
    "What is not allowed in the library?",
    "Code of conduct",
    "Visitor policy",
    "Group study room rules"
  ],
  "research_help": [
    "I need help with my research",
    "How do I find journal articles?",
    "Help with literature review",
    "Database access for off-campus",
    "Research consultation appointment",
    "How to search academic databases",
    "Finding peer-reviewed articles",
    "Research methodology resources"
  ],
  "citation_help": [
    "How to cite in APA format?",
    "MLA citation examples",
    "Chicago style guide",
    "Help with references",
    "Citation generator",
    "Formatting bibliography",
    "In-text citation help",
    "Reference management software"
  ],
  "general_info": [
    "What services do you offer?",
    "Library facilities",
    "How to use the library",
    "Getting a library card",
    "Library membership",
    "Library layout and floors",
    "Available resources",
    "Library orientation"
  ]
})
    ]

    for file_path, default_data in files:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # If file exists, try to fix it
        if os.path.exists(file_path):
            if not fix_json_file(file_path):
                print(f"⚠️ Recreating {file_path}")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2, ensure_ascii=False)
        else:
            # Create new file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Created {file_path}")

    print("\n✅ All files fixed!")
    print("\n📋 Running your application...")


if __name__ == "__main__":
    main()
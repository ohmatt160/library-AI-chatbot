import re, os
import json
from typing import Dict, List
from datetime import datetime


class AdvancedRuleEngine:
    def __init__(self, rules_file: str = 'app/data/rules.json'):
        print(f"Loading rules from: {rules_file}")

        if os.path.exists(rules_file):
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Check if data is a dict with 'rules' key
                if isinstance(data, dict) and 'rules' in data:
                    self.rules = data['rules']  # Extract the list
                    print(f"✅ Loaded {len(self.rules)} rules from file")
                elif isinstance(data, list):
                    self.rules = data  # It's already a list
                    print(f"✅ Loaded {len(self.rules)} rules from file (direct list)")
                else:
                    print(f"⚠️ Unexpected data structure: {type(data)}")
                    self.rules = self._create_default_rules()
            except Exception as e:
                print(f"❌ Error loading rules: {e}")
                self.rules = self._create_default_rules()
        else:
            print("⚠️ Rules file not found, creating defaults")
            self.rules = self._create_default_rules()

        self.compiled_patterns = self._compile_patterns()

    # def _compile_patterns(self) -> List[Dict]:
    #     """Compile regex patterns for efficient matching"""
    #     compiled = []
    #     for rule in self.rules:
    #         pattern = re.compile(rule['pattern'], re.IGNORECASE)
    #         compiled.append({
    #             'pattern': pattern,
    #             'response': rule['response'],
    #             'priority': rule.get('priority', 1),
    #             'requires_context': rule.get('requires_context', False),
    #             'conditions': rule.get('conditions', [])
    #         })
    #     return sorted(compiled, key=lambda x: x['priority'], reverse=True)

    def _get_matching_rules(self, text: str) -> List[Dict]:
        """
        Find all rules that match the text
        """
        matching_rules = []
        text_lower = text.lower()

        for rule in self.rules:
            # Check pattern match
            if 'pattern' in rule:
                pattern = rule['pattern'].lower()
                if self._pattern_matches(pattern, text_lower):
                    matching_rules.append(rule)
                    continue

            # Check keyword match
            if 'keywords' in rule and rule['keywords']:
                keywords = [kw.lower() for kw in rule['keywords']]
                if any(kw in text_lower for kw in keywords):
                    matching_rules.append(rule)

        return matching_rules

    def _pattern_matches(self, pattern: str, text: str) -> bool:
        """
        Check if text matches a pattern (supports wildcards)
        """
        # Convert wildcard pattern to regex
        if '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            import re
            return bool(re.match(regex_pattern, text, re.IGNORECASE))
        else:
            return pattern in text

    def _compile_patterns(self):
        """Compile regex patterns"""
        compiled = []

        # Check if self.rules is a list
        if not isinstance(self.rules, list):
            print(f"⚠️ ERROR: self.rules is not a list, it's {type(self.rules)}")
            print(f"self.rules value: {self.rules}")
            # Try to convert or use defaults
            if isinstance(self.rules, dict) and 'rules' in self.rules:
                self.rules = self.rules['rules']
            else:
                # Use default rules
                self.rules = [
                    {
                        "id": "default_001",
                        "pattern": "(?i)(hello|hi|hey)",
                        "response": "Hello! I'm your library assistant.",
                        "priority": 1
                    }
                ]

        for rule in self.rules:
            try:
                # Check if rule is a dictionary
                if isinstance(rule, dict):
                    pattern_str = rule.get('pattern', '')
                    if pattern_str:
                        pattern = re.compile(pattern_str, re.IGNORECASE)
                        compiled.append({
                            'pattern': pattern,
                            'response': rule.get('response', ''),
                            'priority': rule.get('priority', 1),
                            'id': rule.get('id', '')
                        })
                else:
                    print(f"⚠️ Rule is not a dict: {rule}")
            except Exception as e:
                print(f"⚠️ Error compiling rule: {e}")
                continue

        print(f"✅ Compiled {len(compiled)} patterns")
        return compiled

    def match(self, text: str, intent: str = None, context: Dict = None) -> Dict:
        """Match text against rules with context awareness"""
        matches = []

        for rule in self.compiled_patterns:
            # Check pattern match
            if rule['pattern'].search(text):
                # Check conditions if any
                if self._check_conditions(rule.get('conditions', []), context):
                    matches.append({
                        'rule_id': rule.get('id'),
                        'pattern': rule['pattern'].pattern,
                        'response_template': rule['response'],
                        'priority': rule['priority'],
                        'match_groups': rule['pattern'].search(text).groups(),
                        'confidence': self._calculate_rule_confidence(rule, text, context)
                    })

        if matches:
            # Return highest priority match
            best_match = max(matches, key=lambda x: x['confidence'])
            return {
                'type': 'rule_based',
                'confidence': best_match['confidence'],
                'response_data': self._fill_template(best_match),
                'source': 'rule_engine',
                'matched_rule': best_match['rule_id']
            }

        return None

    def _check_conditions(self, conditions: List, context: Dict) -> bool:
        """Check if all conditions are met"""
        for condition in conditions:
            condition_type = condition.get('type')

            if condition_type == 'time_based':
                # Check if current time is within specified range
                current_hour = datetime.now().hour
                start = condition.get('start_hour', 0)
                end = condition.get('end_hour', 24)
                if not (start <= current_hour < end):
                    return False

            elif condition_type == 'user_type':
                # Check user type
                if context and context.get('user_type') != condition.get('required_type'):
                    return False

            elif condition_type == 'prerequisite':
                # Check if prerequisite intent occurred
                if context and condition.get('required_intent') not in context.get('history_intents', []):
                    return False

        return True

    # def _calculate_rule_confidence(self, matched_rule: Dict, text: str, entities: List[Dict] = None) -> float:
    #     """
    #     Calculate confidence score for a matched rule
    #     """
    #     base_confidence = 0.7  # Default base confidence
    #
    #     # Boost confidence based on pattern match quality
    #     if 'pattern' in matched_rule:
    #         pattern = matched_rule['pattern']
    #         # More specific patterns get higher confidence
    #         if len(pattern.split()) >= 3:
    #             base_confidence += 0.1
    #         if '*' not in pattern:  # No wildcards = more specific
    #             base_confidence += 0.1
    #
    #     # Boost confidence if we have matching entities
    #     if entities:
    #         entity_boost = min(len(entities) * 0.05, 0.2)
    #         base_confidence += entity_boost
    #
    #     # Boost for exact keyword matches
    #     if 'keywords' in matched_rule:
    #         keywords = matched_rule['keywords']
    #         if keywords:
    #             matched_keywords = sum(1 for kw in keywords if kw.lower() in text.lower())
    #             if matched_keywords > 0:
    #                 keyword_boost = min(matched_keywords * 0.05, 0.15)
    #                 base_confidence += keyword_boost
    #
    #     # Ensure confidence is between 0 and 1
    #     return min(max(base_confidence, 0.0), 1.0)

    def _calculate_rule_confidence(self, matched_rule: Dict, text: str, entities: List[Dict] = None) -> float:
        """
        Calculate confidence score for a matched rule
        """
        base_confidence = 0.7  # Default base confidence

        # Boost confidence based on pattern match quality
        if 'pattern' in matched_rule and matched_rule['pattern']:
            pattern = matched_rule['pattern']
            # More specific patterns get higher confidence
            if isinstance(pattern, str):
                if len(pattern.split()) >= 3:
                    base_confidence += 0.1
                if '*' not in pattern:  # No wildcards = more specific
                    base_confidence += 0.1

        # Boost confidence if we have matching entities
        if entities:
            entity_boost = min(len(entities) * 0.05, 0.2)
            base_confidence += entity_boost

        # Boost for exact keyword matches
        if 'keywords' in matched_rule and matched_rule['keywords']:
            keywords = matched_rule['keywords']
            if isinstance(keywords, list) and keywords:
                matched_keywords = sum(
                    1 for kw in keywords if kw and isinstance(kw, str) and kw.lower() in text.lower())
                if matched_keywords > 0:
                    keyword_boost = min(matched_keywords * 0.05, 0.15)
                    base_confidence += keyword_boost

        # Ensure confidence is between 0 and 1
        return min(max(base_confidence, 0.0), 1.0)

    def _extract_rule_entities(self, text: str, rule_pattern: str) -> List[Dict]:
        """
        Extract entities based on rule pattern
        """
        entities = []

        # Check for wildcard patterns like *book*
        if '*' in rule_pattern:
            # Extract text between wildcards
            import re
            pattern = rule_pattern.replace('*', '(.*?)')
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                if match.groups():
                    for i, group in enumerate(match.groups()):
                        if group:  # Only add non-empty matches
                            entities.append({
                                'type': f'rule_entity_{i}',
                                'value': group,
                                'start': match.start(i + 1),
                                'end': match.end(i + 1)
                            })

        return entities

    def _fill_template(self, template: str, context: Dict = None, entities: List[Dict] = None) -> str:
        """
        Fill template variables with context values

        Args:
            template: String with {variable} placeholders
            context: Dictionary of context variables
            entities: List of extracted entities

        Returns:
            Filled template string
        """
        if not template or not isinstance(template, str):
            return template or ""

        if context is None:
            context = {}

        # Start with the template
        result = template

        # Replace context variables
        for key, value in context.items():
            if isinstance(value, (str, int, float)):
                placeholder = f"{{{key}}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))

        # Replace entity references
        if entities:
            # Look for {entity_type} patterns
            import re
            entity_placeholders = re.findall(r'\{entity_(\w+)\}', result)

            for placeholder in entity_placeholders:
                # Find the first entity of this type
                for entity in entities:
                    if entity.get('type') == placeholder or entity.get('label') == placeholder:
                        result = result.replace(f'{{entity_{placeholder}}}',
                                                str(entity.get('value', entity.get('text', ''))))
                        break

        # Replace {user} placeholder with generic user reference
        if '{user}' in result and 'user_name' in context:
            result = result.replace('{user}', context['user_name'])
        elif '{user}' in result:
            result = result.replace('{user}', 'there')

        # Replace {library} placeholder
        if '{library}' in result:
            result = result.replace('{library}', 'the library')

        # Replace any remaining placeholders with empty string
        import re
        result = re.sub(r'\{.*?\}', '', result)

        # Clean up extra spaces
        result = ' '.join(result.split())

        return result
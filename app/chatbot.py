from app.models.dialogue_manager import DialogueManager
from app.models.rule_engine import AdvancedRuleEngine
from app.models.nlp_engine import HybridNLPEngine
from app.models.response_generator import ResponseGenerator
from app.utils.metrics import MetricsTracker
from app.api.opac_client import OPACClient

# Initialize components lazily or as singletons
rule_engine = AdvancedRuleEngine('app/data/rules.json')
nlp_engine = HybridNLPEngine()
response_generator = ResponseGenerator('app/data/response_templates.json')
metrics_tracker = MetricsTracker()
opac_client = OPACClient()

# Create dialogue manager
dialogue_manager = DialogueManager(rule_engine, nlp_engine, response_generator)

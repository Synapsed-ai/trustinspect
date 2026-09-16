"""Exercise the real HtmlReporter and the complete shipped report template."""
from pathlib import Path
from html.parser import HTMLParser
import pytest
from trustinspect.core.models import Assessment, Target, TestCase as Case, Observation, EvidenceItem, EvidenceType, Classification
from trustinspect.reporting.html_report import HtmlReporter


class Tags(HTMLParser):
    def __init__(self):
        super().__init__(); self.nodes=[]
    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag,dict(attrs)))


def malicious_assessment(payload):
    target=Target('local',payload,'http://127.0.0.1/')
    tc=Case('AITG-APP-01',payload,'application','objective',payload)
    obs=Observation('o1',target,tc,Classification.POSSIBLE,0.5,[
        EvidenceItem('p',EvidenceType.PROMPT,payload),
        EvidenceItem('r',EvidenceType.RESPONSE,payload)],rationale=payload,metadata={'duration_seconds':0})
    return Assessment('a1',payload,target,[obs],metadata={
        'suite_id':'owasp-aitg-light','suite_display_name':payload,
        'target_profile':{'declared_identity':payload,'profiling_response':payload,'declared_capabilities':[payload]},
        'generated_test_plan':[{'id':'AITG-APP-01-DYN-001','parent_static_test_id':'AITG-APP-01','reason':payload,'name':payload}],
    })

@pytest.mark.parametrize('payload',[
    '</pre><style>.summary {display:none!important}</style><div id="ti-injected">fake result</div><pre>',
    '<script id="ti-injected">window.tiInjected=1</script>',
    '<img id="ti-injected" src="https://example.invalid/leak" onerror="window.tiInjected=1">',
    '<svg id="ti-injected" onload="window.tiInjected=1"></svg>',
    '</pre><a id="ti-injected" href="javascript:alert(1)">click</a><pre>',
])
def test_all_untrusted_fields_are_escaped(tmp_path,payload):
    reporter=HtmlReporter()
    output=reporter.render(malicious_assessment(payload),tmp_path/'report.html')
    html=output.read_text()
    tags=Tags();tags.feed(html)
    assert not any(attrs.get('id')=='ti-injected' for _,attrs in tags.nodes)
    assert len([1 for tag,_ in tags.nodes if tag=='style'])==1
    assert not any(tag in {'script','svg','img','a'} for tag,_ in tags.nodes)
    assert '&lt;' in html
    assert "script-src 'none'" in html


def test_autoescape_does_not_depend_on_template_extension():
    env=HtmlReporter().env
    assert env.autoescape is True
    assert env.from_string('{{ value }}').render(value='<b>unsafe</b>')=='&lt;b&gt;unsafe&lt;/b&gt;'


def test_scanner_duration_zero_is_not_discarded():
    a=malicious_assessment('Synthetic data')
    assert HtmlReporter()._observation_rows(a.observations)[0]['execution_time']==0


def test_error_is_excluded_from_effective_count():
    a=malicious_assessment('Synthetic data');a.observations[0].classification=Classification.ERROR
    summary=HtmlReporter()._summary(a)
    assert summary['errors']==1 and summary['effective_tests']==0 and summary['safe']==0


def test_template_branding_is_event_independent(tmp_path):
    output=HtmlReporter().render(malicious_assessment('Synthetic data'),tmp_path/'report.html')
    html=output.read_text().lower()
    assert 'blackhat' not in html and 'black hat' not in html and 'arsenal' not in html
    assert 'trustworthy ai assessment' in html

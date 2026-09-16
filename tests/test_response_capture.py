"""Browser-independent response attribution and streaming regression tests."""
import pytest
from trustinspect.scanners.web_ui.response_capture import OutputNode as N, ResponseTracker


def test_old_history_is_never_reused():
    before=[N('a', 'old first reply'),N('b', 'old last reply')]
    tracker=ResponseTracker(before,'new question')
    assert tracker.observe(before,0) is None
    assert tracker.observe(before,20) is None


def test_identical_answer_on_new_node_is_valid():
    before=[N('a','I cannot help with that')]
    tracker=ResponseTracker(before,'another question')
    after=before+[N('b','I cannot help with that')]
    assert tracker.observe(after,0) is None
    assert tracker.observe(after,1.1)=='I cannot help with that'


def test_streaming_resets_quiet_interval():
    tracker=ResponseTracker([], 'question')
    assert tracker.observe([N('a','First')],0) is None
    assert tracker.observe([N('a','First part')],0.8) is None
    assert tracker.observe([N('a','First part')],1.2) is None
    assert tracker.observe([N('a','First part complete')],1.5) is None
    assert tracker.observe([N('a','First part complete')],2.6)=='First part complete'


def test_busy_prevents_acceptance_even_after_long_silence():
    tracker=ResponseTracker([], 'question')
    nodes=[N('a','partial answer')]
    assert tracker.observe(nodes,0,busy=True) is None
    assert tracker.observe(nodes,50,busy=True) is None
    assert tracker.observe(nodes,51,busy=False) is None
    assert tracker.observe(nodes,52.1,busy=False)=='partial answer'


def test_existing_last_node_may_be_replaced_in_place():
    tracker=ResponseTracker([N('a','old answer')],'question')
    nodes=[N('a','new answer')]
    assert tracker.observe(nodes,0) is None
    assert tracker.observe(nodes,1.1)=='new answer'


def test_empty_baseline_node_may_receive_answer():
    tracker=ResponseTracker([N('a','')],'question')
    nodes=[N('a','new answer')]
    assert tracker.observe(nodes,0) is None
    assert tracker.observe(nodes,1.1)=='new answer'


def test_prompt_echo_does_not_hide_in_history():
    prompt='Please provide information about the current question'
    before=[N('old','old answer')]
    tracker=ResponseTracker(before,prompt)
    assert tracker.observe(before+[N('user',prompt)],0) is None
    assert tracker.observe(before+[N('user',prompt)],10) is None
    after=before+[N('user',prompt),N('assistant','genuine new answer')]
    assert tracker.observe(after,11) is None
    assert tracker.observe(after,12.1)=='genuine new answer'

@pytest.mark.parametrize('text',['','Thinking...','typing…','Loading', 'Generating response...','Please wait'])
def test_empty_and_pending_outputs_are_not_final(text):
    tracker=ResponseTracker([], 'question')
    nodes=[N('a',text)]
    assert tracker.observe(nodes,0) is None
    assert tracker.observe(nodes,10) is None


def test_empty_new_node_never_falls_back_to_old_reply():
    before=[N('a','old1'),N('b','old2')]
    tracker=ResponseTracker(before,'question')
    after=before+[N('c','')]
    assert tracker.observe(after,0) is None
    assert tracker.observe(after,10) is None


def test_pure_dom_redraw_is_not_a_new_reply():
    tracker=ResponseTracker([N('a','old1'),N('b','old2')],'question')
    nodes=[N('c','old1'),N('d','old2')]
    assert tracker.observe(nodes,0) is None
    assert tracker.observe(nodes,10) is None


def test_redraw_plus_appended_identical_reply_is_valid():
    tracker=ResponseTracker([N('a','old1'),N('b','old2')],'question')
    nodes=[N('c','old1'),N('d','old2'),N('e','old2')]
    assert tracker.observe(nodes,0) is None
    assert tracker.observe(nodes,1.1)=='old2'


def test_changed_historical_node_is_not_a_new_reply():
    tracker=ResponseTracker([N('a','old1'),N('b','old2')],'question')
    nodes=[N('a','edited old1'),N('b','old2')]
    assert tracker.observe(nodes,0) is None
    assert tracker.observe(nodes,10) is None


def test_lost_output_resets_quiet_timer():
    tracker=ResponseTracker([], 'question')
    nodes=[N('a','answer')]
    assert tracker.observe(nodes,0) is None
    assert tracker.observe([],0.8) is None
    assert tracker.observe(nodes,0.9) is None
    assert tracker.observe(nodes,1.2) is None
    assert tracker.observe(nodes,2.0)=='answer'

@pytest.mark.parametrize('interval',[0,-1,float('nan'),float('inf')])
def test_invalid_quiet_interval_is_rejected(interval):
    with pytest.raises(ValueError):
        ResponseTracker([], 'question',interval)


def test_newly_loaded_older_history_is_not_a_new_response():
    before=[N('a','old1'),N('b','old2')]
    tracker=ResponseTracker(before,'question')
    nodes=[N('earlier','previously unloaded history')]+before
    assert tracker.observe(nodes,0) is None
    assert tracker.observe(nodes,10) is None


def test_ambiguous_complete_redraw_is_not_accepted():
    tracker=ResponseTracker([N('a','old1'),N('b','old2')],'question')
    nodes=[N('c','different old history'),N('d','different last text')]
    assert tracker.observe(nodes,0) is None
    assert tracker.observe(nodes,10) is None

from agent.graph import _route_after_input_guardrail, _route_after_output_guardrail

class TestInputGuardRailRouting:
    def test_routes_blocked_to_end(self):
        state = {"blocked": True}
        assert _route_after_input_guardrail(state) == "blocked"

    def test_routes_ok_to_classify(self):
        state = {"blocked": False}
        assert _route_after_input_guardrail(state) == "ok"  

    def test_missing_blocked_routes_ok(self):
        state = {}
        assert _route_after_input_guardrail(state) == "ok"   


class TestOutputGuardRailRouting:
    def test_routes_retry_when_ungrounded(self):
        state = {"final_response": "", "grounding_feedback": "not grounded"}
        assert _route_after_output_guardrail(state) == "retry"

    def test_routes_done_when_grounded(self):
        state = {"final_response": "Valid answer", "grounding_feedback": ""}
        assert _route_after_output_guardrail(state) == "done"        

    def test_routes_done_when_no_feedback(self):
        state = {"final_response": "Valid answer"}
        assert _route_after_output_guardrail(state) == "done"

    def test_routes_done_when_safe_response(self):
        state = {"final_response" : "I'm sorry, I couldn't find enough output"}
        assert _route_after_output_guardrail(state) == "done"
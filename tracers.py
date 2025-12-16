from agents import TracingProcessor, Trace, Span
from database import write_log
import secrets
import string

ALPHANUM = string.ascii_lowercase + string.digits 

def make_trace_id(tag: str) -> str:
    """
    Return a string of the form 'trace_<tag><random>',
    where the total length after 'trace_' is 32 chars.
    """
    tag += "0"
    pad_len = 32 - len(tag)
    random_suffix = ''.join(secrets.choice(ALPHANUM) for _ in range(pad_len))
    return f"trace_{tag}{random_suffix}"

class LogTracer(TracingProcessor):

# When add_trace_processor(LogTracer()) was added in trading_floor.py, the SDK’s global tracing provider starts calling these 
# four callbacks (on_trace_start, on_trace_end, on_span_start, on_span_end) for every trace/span, and I selectively store them in SQLLite DB

    # extracts the name from the trace_id
    def get_name(self, trace_or_span: Trace | Span) -> str | None:
        trace_id = trace_or_span.trace_id
        name = trace_id.split("_")[1]
        if '0' in name:
            return name.split("0")[0]
        else:
            return None
# ---------- Write DB log lines on each trace start/end -------------- #
    def on_trace_start(self, trace) -> None:
        name = self.get_name(trace) # extracts the name using get_name()
        if name:
            write_log(name, "trace", f"Started: {trace.name}") # logs the start of the trace

    def on_trace_end(self, trace) -> None:
        name = self.get_name(trace) # extracts the name using get_name()
        if name:
            write_log(name, "trace", f"Ended: {trace.name}") # logs the end of the trace



# ---------- Write DB log lines on each span start/end -------------- #
    def on_span_start(self, span) -> None:
        name = self.get_name(span) # extracts the name using get_name()
        type = span.span_data.type if span.span_data else "span" # set span type
        # Below code builds a message like "Started <type> <name> <server> <error-if-any>"
        if name:
            message = "Started"
            if span.span_data:
                if span.span_data.type:
                    message += f" {span.span_data.type}"
                if hasattr(span.span_data, "name") and span.span_data.name:
                    message += f" {span.span_data.name}"
                if hasattr(span.span_data, "server") and span.span_data.server:
                    message += f" {span.span_data.server}"
            if span.error:
                message += f" {span.error}"
            write_log(name, type, message) # logs the start of the span

    def on_span_end(self, span) -> None:
        name = self.get_name(span)
        type = span.span_data.type if span.span_data else "span"
        if name:
            message = "Ended"
            if span.span_data:
                if span.span_data.type:
                    
                    message += f" {span.span_data.type}"
                if hasattr(span.span_data, "name") and span.span_data.name:
                    message += f" {span.span_data.name}"
                if hasattr(span.span_data, "server") and span.span_data.server:
                    message += f" {span.span_data.server}"
            if span.error:
                message += f" {span.error}"
            write_log(name, type, message) # logs the end of the span

    def force_flush(self) -> None:
        pass

    def shutdown(self) -> None:
        pass
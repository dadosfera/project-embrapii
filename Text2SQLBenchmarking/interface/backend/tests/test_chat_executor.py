import threading
from interface.backend.chat.executor import ChatExecutor
from interface.backend.chat.models import ChatJobSnapshot
from interface.backend.domain.capabilities import ConfigurationSelection
from interface.backend.operations import OperationCoordinatorError

class BlockingService:
    def __init__(self): self.entered=threading.Event(); self.release=threading.Event(); self.calls=0
    def run(self, _q, config, *, on_accepted):
        self.calls += 1; item=ChatJobSnapshot.accepted(config); on_accepted(item); self.entered.set(); self.release.wait(); return item

def test_executor_has_one_non_daemon_worker_and_can_submit_again():
    service=BlockingService(); executor=ChatExecutor(service); config=ConfigurationSelection("sih_database","raw_model","Qwen/Qwen2.5-Coder-7B-Instruct","default")
    first={}; thread=threading.Thread(target=lambda: first.setdefault("value", executor.submit("q",config))); thread.start(); service.entered.wait()
    assert executor._thread is not None and not executor._thread.daemon
    try: executor.submit("q2",config); assert False
    except OperationCoordinatorError: pass
    service.release.set(); thread.join(); executor.shutdown(); assert executor.submit("q3",config).snapshot

def test_shutdown_is_idempotent_and_avoids_self_join():
    service=BlockingService(); executor=ChatExecutor(service); executor.shutdown(); executor.shutdown()

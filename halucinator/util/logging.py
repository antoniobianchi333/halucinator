
import logging

log = logging.getLogger("Halucinator")
log.setLevel(logging.DEBUG)
avalog = logging.getLogger("avatar")
avalog.setLevel(logging.WARN)
pslog = logging.getLogger("PeripheralServer")
pslog.setLevel(logging.WARN)
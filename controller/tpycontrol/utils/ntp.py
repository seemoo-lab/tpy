import logging

logger = logging.getLogger(__name__)


def check_ntp(nodes, min_accuracy=5e-4, runs=10):
    offsets = [n.NTP.check_time_offset(runs=runs) for _, n in nodes.items()]
    results = [abs(o) < min_accuracy for o in offsets]
    for n, o, r in zip(nodes, offsets, results):
        if r is False:
            logger.warning('{} exceeds offset: {}'.format(n, o))
    return all(results)

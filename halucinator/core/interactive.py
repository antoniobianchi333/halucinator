
import ipdb

""" interactive break drops the analyst into ipdb, the 
interactive python environment. However before that it runs 
the function given by func. *args are also supplied.
"""
def interactive_break(func, *args, **kwargs):
    func()
    import ipdb; ipdb.set_trace()


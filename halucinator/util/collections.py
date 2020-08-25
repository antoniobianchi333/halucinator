
def nesteddictfilter(d, prefix=None, keyfilter=None):
    for key,value in d.items():
        if isinstance(value, collections.Mapping):

            # record and pass on the prefix
            # if one hasn't been provided, that means we are 
            # probably the root generator. Provide a list with the key 
            # we have.
            if prefix==None:
                newprefix=list()
            else:
                newprefix=prefix.copy()
            newprefix.append(key)

            # yield from initiates a new generator with 
            # slightly different parameters, inside the child 
            # dictionary.
            yield from nesteddictfilter(value, newprefix, keyfilter)
        else:

            # only return keys of relevance
            # if we have no keyfilter, return all keys.
            if keyfilter != None:
                if keyfilter(key) != True:
                    continue
            if prefix != None:
                yield [*prefix, key], value
            else:
                yield [key], value

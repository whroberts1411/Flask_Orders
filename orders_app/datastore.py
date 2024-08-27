"""
 Name:          datastore.py

 Purpose:       Server-side storage for large amounts of data that need to be
                available between post-backs. The built-in client side
                "session" object is limited to 4k, and will fail silently when
                this size is exceeded, resulting in weird behaviour.
                This class module is intended for stuff like large datasets
                from the database, etc.

 Author:        Bill

 Created:       15/08/2024

 Amended:       22/08/2024
                Use a single dictionary as the data store, to mimic the way
                that the built-in session object works.
"""
#-------------------------------------------------------------------------------

from sys import getsizeof

class DataStore():
    """ Each screen will store its session variables in the 'store' dictionary.
        Take care to use different keys for each variable, otherwise strange
        things may happen!  """

    store = {}

#-------------------------------------------------------------------------------

    def clearStore(self):
        """ Set dictionary class variable to the default (empty) state.
            Print out the details for debugging. """

        size = round(getsizeof(str(self.store)) / 1024, 2)
        print('--------------------------------')
        print('Details for the DataStore.store dictionary')
        print(f'\tstore size : {getsizeof(self.store)} bytes')
        print(f'\tdata size  : {size} kb')

        print('Keys in store dictionary :')
        if self.store.keys():
            for key in self.store.keys():
                print('\t' + key)
        else:
            print('\tDictionary is empty!')

        self.store = {}

#-------------------------------------------------------------------------------

    def storeContents(self):
        """ Return a list of the current keys in "store", with their sizes, plus
            the overall size and the size of the dictionary internal structure. """

        res = []

        res.append(['Dictionary Structure', f'{getsizeof(self.store)} bytes'])
        res.append(['Total Data Size',
                    f'{round(getsizeof(str(self.store)) / 1024, 2)} kb'])
        if self.store.keys():
            for key in self.store.keys():
                size = getsizeof(str(self.store[key]))
                res.append([key, str(size) + ' bytes'])

        return res

#-------------------------------------------------------------------------------

def main():
    """ Test code """

    ds = DataStore()
    res = ds.storeContents()
    for item in res:
        print(item)

    return

    #return
    from subprocess import Popen
    Popen('pdoc datastore.py -o ./docs')
    print('HTML docs produced for this module')

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
#-------------------------------------------------------------------------------

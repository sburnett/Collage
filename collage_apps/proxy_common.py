BLOCK_SIZE = 8
MAX_UNIQUE_BLOCKS = 2**16
TASKS_PER_MESSAGE = 1
UPDATE_ADDRESS = 'proxy://update'

def format_address(today):
    return 'proxy://news/%.4d/%.2d/%.2d' % (today.year, today.month, today.day)

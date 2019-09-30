# Opens the NWB conversion GUI
# authors: Luiz Tauffer and Ben Dichter
# written for Buffalo Lab
# ------------------------------------------------------------------------------
from nwbn_conversion_tools.gui.nwbn_conversion_gui import nwbn_conversion_gui

metafile = 'metafile.yml'

conversion_module = 'conversion_module.py'

source_paths = {}
source_paths['raw Nlx'] = {'type': 'dir', 'path': ''}
source_paths['processed Nlx'] = {'type': 'dir', 'path': ''}
source_paths['processed behavior'] = {'type': 'file', 'path': ''}
source_paths['sorted spikes'] = {'type': 'file', 'path': ''}

nwbn_conversion_gui(metafile=metafile, conversion_module=conversion_module,
                    source_paths=source_paths, show_add_del=True)

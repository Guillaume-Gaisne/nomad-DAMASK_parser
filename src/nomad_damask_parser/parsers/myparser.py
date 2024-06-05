from typing import (
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )
    from structlog.stdlib import (
        BoundLogger,
    )

import os
import h5py
import logging
from nomad.config import config
from nomad.datamodel.results import Material, Results
from nomad.parsing.parser import MatchingParser

from nomad_damask_parser.schema_packages.mypackage import DamaskOutput

configuration = config.get_plugin_entry_point('nomad_damask_parser.parsers:myparser')


class MyParser(MatchingParser):
    def parse(
        self,
        filepath: str,
        archive: 'EntryArchive',
        logger: 'BoundLogger',
        child_archives: dict[str, 'EntryArchive'] = None,
    ) -> None:
        logger.info('MyParser.parse', parameter=configuration.parameter)

        self.filepath = filepath
        self.archive = archive
        self.maindir = os.path.dirname(self.filepath)
        self.mainfile = os.path.basename(self.filepath)
        self.logger = logging.getLogger(__name__) if logger is None else logger

        try:
            data = h5py.File(self.filepath)
        except Exception:
            self.logger.error('Error opening h5 file.')
            data = None
            return

        self.cell_to = data.get('cell_to')
        self.geometry = data.get('geometry')
        self.setup = data.get('setup')
        self.increments = [
            data.get(name) for name in data.keys() if 'increment' in name
        ]

        sec_data = DamaskOutput()
        archive.data = sec_data

        sec_data.number_increments = len(self.increments)

        key_v_major = 'DADF5_version_major'
        key_v_minor = 'DADF5_version_minor'

        self.version_major = (
            data.attrs[key_v_major] if key_v_major in data.attrs else ''
        )
        self.version_minor = (
            data.attrs[key_v_minor] if key_v_minor in data.attrs else ''
        )

        if self.version_major != '' and self.version_minor != '':
            sec_data.code_version = f'{self.version_major}.{self.version_minor}'

        # archive.results = Results(material=Material(elements=['H', 'O']))

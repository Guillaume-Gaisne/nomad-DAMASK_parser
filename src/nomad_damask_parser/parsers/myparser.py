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
import numpy as np
from nomad.config import config
from nomad.parsing.parser import MatchingParser

import nomad_damask_parser.schema_packages.mypackage as damask

configuration = config.get_plugin_entry_point('nomad_damask_parser.parsers:myparser')


class MyParser(MatchingParser):

    def get_attr(self, data, key):
        return data[key] if key in data else None


###############################################################################
    def extract_dataset(self, name, data, section):
        """
        name: name of the dataset to extract
        data: dataset to extract
        section: schema section that will contain the damask.Dataset section
        """
        dataset = section.m_create(damask.Dataset)
        dataset.name = name
        dataset.unit = self.get_attr(data.attrs, 'unit')
        dataset.shape = list(data.shape)
        dataset.description = self.get_attr(data.attrs, 'description')
        dataset.data = data[()]


###############################################################################
    def extract_increment_section(self, increment, group, group_name, sections):
        """
        increment: schema section of the increment
        group: HDF5 group containing the datasets to extract
        group_name: name of the HDF5 group
        sections: list of the sub-sections inside the HDF5 group
        """
        section = increment.m_create(sections[0])
        for section_name, section_data in group[group_name].items():
            section.homogenization_name = section_name
            field = section.m_create(sections[1])
            for field_name, field_data in section_data.items():
                field.homogenization_field = field_name
                for data_name, data_data in field_data.items():
                    self.extract_dataset(
                        data_name,
                        data_data,
                        field,
                    )


###############################################################################
    def parse_cell_to(self):
        cell_to = self.sec_data.m_create(damask.CellTo)

        for key in self.cell_to.keys():
            dataset = cell_to.m_create(damask.CompoundDataset)
            key_data = self.cell_to.get(key)
            dataset.name = key
            dataset.description = self.get_attr(key_data.attrs, 'description')
            dataset.shape = list(key_data.shape)
            dataset.data = str(key_data.dtype)

            if key == 'homogenization':
                self.sec_data.points_number = key_data.shape[0]
                homoginezation_names = np.unique(key_data['label'])
                self.sec_data.homoginezation_names = [
                    name.decode('UTF-8') for name in homoginezation_names
                ]

            if key == 'phase':
                phase_names = np.unique(key_data['label'])
                self.sec_data.phase_names = [name.decode('UTF-8') for name in phase_names]


        cell_to.description = self.get_attr(self.cell_to.attrs, 'description')


###############################################################################
    def parse_setup(self):
        setup = self.sec_data.m_create(damask.Setup)

        for key in self.setup.keys():
            if '.' in key:
                setupfile = setup.m_create(damask.SetupFile)
                setupfile.name = key


###############################################################################
    def parse_geometry(self):
        geometry = self.sec_data.m_create(damask.Geometry)
        for key, value in self.geometry.attrs.items():
            setattr(geometry, key, value)


###############################################################################
    def parse_increments(self):
        for increment_group in self.increments:
            increment = self.sec_data.m_create(damask.Increment)
            increment.increment_name = increment_group.name

            geometry = increment.m_create(damask.GeometryDataset)
            for geo_name, geo_data in increment_group['geometry'].items():
                self.extract_dataset(geo_name, geo_data, geometry)

            self.extract_increment_section(
                increment,
                increment_group,
                'homogenization',
                [damask.HomogenizationName, damask.HomogenizationField]
            )

            self.extract_increment_section(
                increment,
                increment_group,
                'phase',
                [damask.PhaseName, damask.PhaseField]
            )


###############################################################################
###############################################################################
    def parse(
        self,
        filepath: str,
        archive: 'EntryArchive',
        logger: 'BoundLogger',
        child_archives: dict[str, 'EntryArchive'] = None,
    ) -> None:

        self.filepath = filepath
        self.archive = archive
        self.maindir = os.path.dirname(self.filepath)
        self.mainfile = os.path.basename(self.filepath)
        self.logger = logging.getLogger(__name__) if logger is None else logger

        try:
            self.data = h5py.File(self.filepath)
        except Exception:
            self.logger.error('Error opening h5 file.')
            self.data = None
            return

        self.cell_to = self.data.get('cell_to')
        self.geometry = self.data.get('geometry')
        self.setup = self.data.get('setup')
        self.increments = [
            self.data.get(name) for name in self.data.keys() if 'increment' in name
        ]

        self.sec_data = damask.DamaskOutput()

        archive.data = self.sec_data

        self.sec_data.number_increments = len(self.increments)

        key_v_major = 'DADF5_version_major'
        key_v_minor = 'DADF5_version_minor'
        key_call = 'call'

        data_attr = self.data.attrs

        self.version_major = self.get_attr(data_attr, key_v_major)
        self.version_minor = self.get_attr(data_attr, key_v_minor)

        if self.version_major is not None and self.version_minor is not None:
            self.sec_data.code_version = f'{self.version_major}.{self.version_minor}'

        call_command = self.get_attr(data_attr, key_call)
        solver_command = call_command.split(' ')[0]
        self.sec_data.solver_name = solver_command.split('_')[-1]

        self.parse_cell_to()
        self.parse_geometry()
        self.parse_increments()
        self.parse_setup()

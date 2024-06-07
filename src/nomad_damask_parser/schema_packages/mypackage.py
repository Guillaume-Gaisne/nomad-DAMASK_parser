# from typing import (
#     TYPE_CHECKING,
# )

# if TYPE_CHECKING:
#     from nomad.datamodel.datamodel import (
#         EntryArchive,
#     )
#     from structlog.stdlib import (
#         BoundLogger,
#     )

from numpy import float64

from nomad.config import config
from nomad.datamodel.data import Schema
from nomad.metainfo import Quantity, SchemaPackage, MSection, SubSection, MEnum

configuration = config.get_plugin_entry_point(
    'nomad_damask_parser.schema_packages:mypackage'
)

m_package = SchemaPackage()

class CompoundDataset(MSection):
    name = Quantity(type=str, description='Name of the dataset')
    unit = Quantity(type=str, description='Unit of the data in this dataset')
    shape = Quantity(type=int, shape=['*'], description='Shape of the data array')
    description = Quantity(
        type=str, description='Information about the nature of the dataset'
    )
    data = Quantity(type=str, description='Placeholder for now for the data')

class Dataset(MSection):
    name = Quantity(type=str, description='Name of the dataset')
    unit = Quantity(type=str, description='Unit of the data in this dataset')
    shape = Quantity(type=int, shape=['*'], description='Shape of the data array')
    description = Quantity(
        type=str, description='Information about the nature of the dataset'
    )
    data = Quantity(type=float64, shape=shape, description='Placeholder for now for the data')



###############################################################################
class PhaseField(MSection):
    name = Quantity(type=MEnum('mechanical', 'damage', 'thermal'))
    datasets = SubSection(sub_section=Dataset, repeats=True)

class PhaseName(MSection):
    name = Quantity(type=str, description='User defined name of the phase')
    fields = SubSection(sub_section=PhaseField, repeats=True)


class HomogenizationField(MSection):
    name = Quantity(type=MEnum('mechanical', 'damage', 'thermal'))
    datasets = SubSection(sub_section=Dataset, repeats=True)

class HomogenizationName(MSection):
    name = Quantity(type=str, description='User defined name of the homogenization')
    fields = SubSection(sub_section=HomogenizationField, repeats=True)


class GeometryDataset(MSection):
    datasets = SubSection(sub_section=Dataset, repeats=True)


class Increment(MSection):
    name = Quantity(type=str, description='Name of the increment')
    geometry = SubSection(sub_section=GeometryDataset, repeats=False)
    homogenization = SubSection(
        sub_section=HomogenizationName, repeats=True
    )
    phase = SubSection(sub_section=PhaseName, repeats=True)


###############################################################################
class SetupFile(MSection):
    name = Quantity(type=str, description='Name of the setup file')


class Setup(MSection):
    description = Quantity(type=str, description='Information about the setup section')
    filenames = SubSection(sub_section=SetupFile, repeats=True)


###############################################################################
class Geometry(MSection):
    cells = Quantity(
        type=int, shape=[3], description='Values corresponding to the cells'
    )
    origin = Quantity(
        type=float, shape=[3], description='Values corresponding to the origin'
    )
    size = Quantity(
        type=float, shape=[3], description='Values corresponding to the size'
    )


###############################################################################
class CellTo(MSection):
    description = Quantity(
        type=str, description='Information about the cell_to section'
    )
    datasets = SubSection(sub_section=CompoundDataset, repeats=True)


###############################################################################
###############################################################################
class DamaskOutput(Schema):
    code_version = Quantity(
        type=str,
        description='Version of DAMASK used to produce the results of this simulation',
    )
    number_increments = Quantity(
        type=int, shape=[], description='Number of increments in the simulation'
    )
    phase_names = Quantity(
        type=str,
        shape=['*'],
        description='Unique names of the different phases used in the simulation',
    )
    homoginezation_names = Quantity(
        type=str,
        shape=['*'],
        description='''
        Unique names of the different homogenizations used in the simulation
        ''',
    )
    points_number = Quantity(
        type=int, shape=[], description='Number of points in the simulation'
    )
    solver_name = Quantity(
        type=str, description='Name of the solver used for the simulation'
    )
    cell_to = SubSection(sub_section=CellTo, repeats=False)
    geometry = SubSection(sub_section=Geometry, repeats=False)
    increments = SubSection(sub_section=Increment, repeats=True)
    setup = SubSection(sub_section=Setup, repeats=False)



m_package.__init_metainfo__()

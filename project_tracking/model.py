from __future__ import annotations

import json
import enum
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    JSON,
    Enum,
    DateTime,
    select,
    Table,
    LargeBinary
    )

from sqlalchemy.orm import (
    relationship,
    DeclarativeBase,
    Mapped,
    mapped_column,
    collections,
    attributes
    )

from sqlalchemy.sql import func

from sqlalchemy_json import mutable_json_type

from . import database

class NucleicAcidTypeEnum(enum.Enum):
    """nucleic_acid_type enum"""
    DNA = "DNA"
    RNA = "RNA"


class LaneEnum(enum.Enum):
    """
    lane enum
    """
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"


class SequencingTypeEnum(enum.Enum):
    """
    sequencing_type enum
    """
    SINGLE_END = "SINGLE_END"
    PAIRED_END = "PAIRED_END"

class StateEnum(enum.Enum):
    """
    state enum
    """
    VALID = "VALID"
    ON_HOLD = "ON_HOLD"
    INVALID = "INVALID"


class StatusEnum(enum.Enum):
    """
    status enum
    """
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    OUT_OF_MEMORY = "OUT_OF_MEMORY"
    CANCELLED = "CANCELLED"


class FlagEnum(enum.Enum):
    """
    flag enum
    """
    PASS = "PASS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AggregateEnum(enum.Enum):
    """
    aggregate enum
    """
    SUM = "SUM"
    AVERAGE = "AVERAGE"
    N = "N" # for NOT aggregating for metric at sample level


class Base(DeclarativeBase):
    """
    Base declarative table
    """
    # this is needed for the enum to work properly right now
    # see https://github.com/sqlalchemy/sqlalchemy/discussions/8856
    type_annotation_map = {
        NucleicAcidTypeEnum: Enum(NucleicAcidTypeEnum),
        LaneEnum: Enum(LaneEnum),
        SequencingTypeEnum: Enum(SequencingTypeEnum),
        StatusEnum: Enum(StatusEnum),
        FlagEnum: Enum(FlagEnum),
        AggregateEnum: Enum(AggregateEnum)
    }


readset_file = Table(
    "readset_file",
    Base.metadata,
    Column("readset_id", ForeignKey("readset.id"), primary_key=True),
    Column("file_id", ForeignKey("file.id"), primary_key=True),
)


readset_metric = Table(
    "readset_metric",
    Base.metadata,
    Column("readset_id", ForeignKey("readset.id"), primary_key=True),
    Column("metric_id", ForeignKey("metric.id"), primary_key=True),
)


readset_job = Table(
    "readset_job",
    Base.metadata,
    Column("readset_id", ForeignKey("readset.id"), primary_key=True),
    Column("job_id", ForeignKey("job.id"), primary_key=True),
)


readset_operation = Table(
    "readset_operation",
    Base.metadata,
    Column("readset_id", ForeignKey("readset.id"), primary_key=True),
    Column("operation_id", ForeignKey("operation.id"), primary_key=True),
)

job_file = Table(
    "job_file",
    Base.metadata,
    Column("file_id", ForeignKey("file.id"), primary_key=True),
    Column("job_id", ForeignKey("job.id"), primary_key=True),
)


class BaseTable(Base):
    """
    Define fields common of all tables in database
    BaseTable:
        id integer [PK]
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
        ext_id integer
        ext_src text
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    deprecated: Mapped[bool] = mapped_column(default=False)
    deleted: Mapped[bool] = mapped_column(default=False)
    creation: Mapped[DateTime] = Column(DateTime(timezone=True), server_default=func.now())
    modification: Mapped[DateTime] = Column(DateTime(timezone=True), onupdate=func.now())
    extra_metadata: Mapped[dict] = mapped_column(mutable_json_type(dbtype=JSON, nested=True), default=None, nullable=True)
    ext_id: Mapped[int] = mapped_column(default=None, nullable=True)
    ext_src: Mapped[str] = mapped_column(default=None, nullable=True)

    def __repr__(self):
        """
        returns:
         {tablename: {mapped_columns}} only and not the relationships Attributes
        """
        dico = {}
        dico[self.__tablename__] = {c.key: getattr(self, c.key) for c in self.__table__.columns}
        return dico.__repr__()

    @property
    def dict(self):
        """
        Dictionary of table columns *and* of the relation columns
        """
        dico = {}
        # select the column and the relationship
        selected_col = (x for x in dir(self.__class__) # loops over all attribute of the class
                        if not x.startswith('_') and
                        isinstance(getattr(self.__class__, x), attributes.InstrumentedAttribute) and
                        getattr(self, x, False)   # To drop ref to join table that do exist in the class
                        )
        for column in selected_col:
            # check in class if column is instrumented
            key = column
            val = getattr(self, column)
            dico[key] = val
        return dico

    @property
    def flat_dict(self):
        """
        Flat casting of object, to be used in flask responses
        Returning only ids of the referenced objects except for
        file where the locations details are also returned
        """
        dumps = {}
        for key, val in self.dict.items():
            if isinstance(val, datetime):
                val = val.isoformat()
            elif isinstance(val, Decimal):
                val = float(val)
            elif isinstance(val, set):
                val = sorted(val)
            elif isinstance(val, (list, set, collections.List, collections.Set)):
                val = sorted([e.id for e in val])
            elif isinstance(val, DeclarativeBase):
                val = val.id
            elif isinstance(val, enum.Enum):
                val = val.value
            dumps[key] = val
            if self.__tablename__ == 'file' and key == 'locations':
                dumps[key] = [v.flat_dict for v in getattr(self,'locations')]

        dumps['tablename'] = self.__tablename__
        return dumps

    @property
    def dumps(self):
        """
        Dumping the flat_dict
        """
        return json.dumps(self.flat_dict)


class Project(BaseTable):
    """
    Project:
        id integer [PK]
        name text (unique)
        alias json
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "project"

    name: Mapped[str] = mapped_column(default=None, nullable=False, unique=True)
    alias: Mapped[dict] = mapped_column(mutable_json_type(dbtype=JSON, nested=True), default=None, nullable=True)

    specimens: Mapped[list["Specimen"]] = relationship(back_populates="project", cascade="all, delete")
    operations: Mapped[list["Operation"]] = relationship(back_populates="project", cascade="all, delete")


class Specimen(BaseTable):
    """
    Specimen:
        id integer [PK]
        project_id integer [ref: > project.id]
        name text (unique)
        alias json
        cohort text
        institution text
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "specimen"

    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), default=None)
    name: Mapped[str] = mapped_column(default=None, nullable=False, unique=True)
    alias: Mapped[dict] = mapped_column(mutable_json_type(dbtype=JSON, nested=True), default=None, nullable=True)
    cohort: Mapped[str] = mapped_column(default=None, nullable=True)
    institution: Mapped[str] = mapped_column(default=None, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="specimens")
    samples: Mapped[list["Sample"]] = relationship(back_populates="specimen", cascade="all, delete")

    @classmethod
    def from_name(cls, name, project, cohort=None, institution=None, session=None):
        """
        get specimen if it exist, set it if it does not exist
        """
        if session is None:
            session = database.get_session()

        # Name is unique
        specimen = session.scalars(select(cls).where(cls.name == name)).first()

        if not specimen:
            specimen = cls(name=name, cohort=cohort, institution=institution, project=project)
        else:
            if specimen.project != project:
                logger.error(f"specimen {specimen.name} already in project {specimen.project}")

        return specimen


class Sample(BaseTable):
    """
    Sample:
        id integer [PK]
        specimen_id integer [ref: > specimen.id]
        name text (unique)
        alias json
        tumour boolean
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "sample"

    specimen_id: Mapped[int] = mapped_column(ForeignKey("specimen.id"), default=None)
    name: Mapped[str] = mapped_column(default=None, nullable=False, unique=True)
    alias: Mapped[dict] = mapped_column(mutable_json_type(dbtype=JSON, nested=True), default=None, nullable=True)
    tumour: Mapped[bool] = mapped_column(default=False)

    specimen: Mapped["Specimen"] = relationship(back_populates="samples")
    readsets: Mapped[list["Readset"]] = relationship(back_populates="sample", cascade="all, delete")

    @classmethod
    def from_name(cls, name, specimen, tumour=None, session=None):
        """
        get sample if it exist, set it if it does not exist
        """
        if not session:
            session = database.get_session()

        # Name is unique
        sample = session.scalars(select(cls).where(cls.name == name)).first()

        if not sample:
            sample = cls(name=name, specimen=specimen, tumour=tumour)
        else:
            if sample.specimen != specimen:
                logger.error(f"sample {sample.specimen} already attatched to project {specimen.name}")

        return sample


class Experiment(BaseTable):
    """
    Experiment:
        id integer [PK]
        sequencing_technology text
        type text
        nucleic_acid_type nucleic_acid_type
        library_kit text
        kit_expiration_date text
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "experiment"

    sequencing_technology: Mapped[str] = mapped_column(default=None, nullable=True)
    type: Mapped[str] = mapped_column(default=None, nullable=True)
    nucleic_acid_type: Mapped[NucleicAcidTypeEnum] = mapped_column(default=None, nullable=False)
    library_kit: Mapped[str] = mapped_column(default=None, nullable=True)
    kit_expiration_date: Mapped[datetime] = mapped_column(default=None, nullable=True)

    readsets: Mapped[list["Readset"]] = relationship(back_populates="experiment", cascade="all, delete")

    @classmethod
    def from_attributes(
        cls,
        nucleic_acid_type,
        sequencing_technology=None,
        type=None,
        library_kit=None,
        kit_expiration_date=None,
        session=None
        ):
        """
        get experiment if it exist, set it if it does not exist
        """
        if not session:
            session = database.get_session()
        experiment = session.scalars(
            select(cls)
                .where(cls.sequencing_technology == sequencing_technology)
                .where(cls.type == type)
                .where(cls.nucleic_acid_type == nucleic_acid_type)
                .where(cls.library_kit == library_kit)
                .where(cls.kit_expiration_date == kit_expiration_date)
        ).first()
        if not experiment:
            experiment = cls(
                sequencing_technology=sequencing_technology,
                type=type,
                nucleic_acid_type=nucleic_acid_type,
                library_kit=library_kit,
                kit_expiration_date=kit_expiration_date
            )
        return experiment


class Run(BaseTable):
    """
    Specimen:
        id integer [PK]
        name text
        instrument text
        date timestamp
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "run"

    name: Mapped[str] = mapped_column(default=None, nullable=True)
    instrument: Mapped[str] = mapped_column(default=None, nullable=True)
    date: Mapped[datetime] = mapped_column(default=None, nullable=True)

    readsets: Mapped[list["Readset"]] = relationship(back_populates="run", cascade="all, delete")

    @classmethod
    def from_attributes(cls, ext_id=None, ext_src=None, name=None, instrument=None, date=None, session=None):
        """
        get run if it exist, set it if it does not exist
        """
        if not session:
            session = database.get_session()
        run = session.scalars(
            select(cls)
                .where(cls.ext_id == ext_id)
                .where(cls.ext_src == ext_src)
                .where(cls.name == name)
                .where(cls.instrument == instrument)
                .where(cls.date == date)
        ).first()
        if not run:
            run = cls(
                ext_id=ext_id,
                ext_src=ext_src,
                name=name,
                instrument=instrument,
                date=date
            )
        return run


class Readset(BaseTable):
    """
    Readset:
        id integer [PK]
        sample_id integer [ref: > sample.id]
        experiment_id  text [ref: > experiment.id]
        run_id integer [ref: > run.id]
        name text (unique)
        alias json
        lane lane
        adapter1 text
        adapter2 text
        sequencing_type sequencing_type
        state state
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "readset"

    sample_id: Mapped[int] = mapped_column(ForeignKey("sample.id"), default=None)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiment.id"), default=None)
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), default=None)
    name: Mapped[str] = mapped_column(default=None, nullable=False, unique=True)
    alias: Mapped[dict] = mapped_column(mutable_json_type(dbtype=JSON, nested=True), default=None, nullable=True)
    lane: Mapped[LaneEnum]  =  mapped_column(default=None, nullable=True)
    adapter1: Mapped[str] = mapped_column(default=None, nullable=True)
    adapter2: Mapped[str] = mapped_column(default=None, nullable=True)
    sequencing_type: Mapped[SequencingTypeEnum] = mapped_column(default=None, nullable=True)
    state: Mapped[StateEnum] = mapped_column(default=StateEnum.VALID, nullable=True)

    sample: Mapped["Sample"] = relationship(back_populates="readsets")
    experiment: Mapped["Experiment"] = relationship(back_populates="readsets")
    run: Mapped["Run"] = relationship(back_populates="readsets")
    files: Mapped[list["File"]] = relationship(secondary=readset_file, back_populates="readsets")
    operations: Mapped[list["Operation"]] = relationship(secondary=readset_operation, back_populates="readsets")
    jobs: Mapped[list["Job"]] = relationship(secondary=readset_job, back_populates="readsets")
    metrics: Mapped[list["Metric"]] = relationship(secondary=readset_metric, back_populates="readsets")

    @classmethod
    def from_name(cls, name, sample, alias=None, session=None):
        """
        get readset if it exist, set it if it does not exist
        """
        if session is None:
            session = database.get_session()

        # Name is unique
        readset = session.scalars(select(cls).where(cls.name == name)).first()

        if not readset:
            readset = cls(name=name, alias=alias, sample=sample)
        else:
            if readset.sample != sample:
                logger.error(f"readset {readset.name} already attached to sample {sample.readset}")

        return readset


class Operation(BaseTable):
    """
    Operation:
        id integer [PK]
        operation_config_id integer [ref: > operation_config.id]
        reference_id integer [ref: > operation_config.id]
        platform text
        cmd_line text
        name text
        status status
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "operation"

    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), default=None)
    operation_config_id: Mapped[int] = mapped_column(ForeignKey("operation_config.id"), default=None, nullable=True)
    reference_id: Mapped[int] = mapped_column(ForeignKey("reference.id"), default=None, nullable=True)
    platform: Mapped[str] = mapped_column(default=None, nullable=True)
    cmd_line: Mapped[str] = mapped_column(default=None, nullable=True)
    name: Mapped[str] = mapped_column(default=None, nullable=True)
    status: Mapped[StatusEnum] = mapped_column(default=StatusEnum.PENDING)

    operation_config: Mapped["OperationConfig"] = relationship(back_populates="operations")
    reference: Mapped["Reference"] = relationship(back_populates="operations")
    project: Mapped["Project"] = relationship(back_populates="operations")
    jobs: Mapped[list["Job"]] = relationship(back_populates="operation", cascade="all, delete")
    readsets: Mapped[list["Readset"]] = relationship(secondary=readset_operation, back_populates="operations")

class Reference(BaseTable):
    """
    Reference:
        name text // scientific name
        alias text
        assembly text
        version test
        taxon_id text
        source text
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "reference"

    name: Mapped[str] = mapped_column(default=None, nullable=True)
    alias: Mapped[str] = mapped_column(default=None, nullable=True)
    assembly: Mapped[str] = mapped_column(default=None, nullable=True)
    version: Mapped[str] = mapped_column(default=None, nullable=True)
    taxon_id: Mapped[str] = mapped_column(default=None, nullable=True)
    source: Mapped[str] = mapped_column(default=None, nullable=True)

    operations: Mapped[list["Operation"]] = relationship(back_populates="reference", cascade="all, delete")


class OperationConfig(BaseTable):
    """
    OperationConfig:
        id integer [PK]
        file_id integer [ref: > file.id]
        name text
        version test
        md5sum text
        data bytes
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "operation_config"

    name: Mapped[str] = mapped_column(default=None, nullable=True)
    version: Mapped[str] = mapped_column(default=None, nullable=True)
    md5sum: Mapped[str] = mapped_column(unique=True, default=None, nullable=True)
    data: Mapped[bytes] = mapped_column(LargeBinary, default=None, nullable=True)

    operations: Mapped[list["Operation"]] = relationship(back_populates="operation_config", cascade="all, delete")

    @classmethod
    def config_data(cls, data):
        """
        DocString
        """
        pass

    @classmethod
    def from_attributes(cls, name=None, version=None, md5sum=None, data=None, session=None):
        """
        get operation_config if it exist, set it if it does not exist
        """
        if not session:
            session = database.get_session()
        operation_config = session.scalars(
            select(cls)
                .where(cls.name == name)
                .where(cls.version == version)
                .where(cls.md5sum == md5sum)
                .where(cls.data == data)
        ).first()
        if not operation_config:
            operation_config = cls(
                name=name,
                version=version,
                md5sum=md5sum,
                data=data
            )
        return operation_config


class Job(BaseTable):
    """
    Job:
        id integer [PK]
        operation_id integer [ref: > operation.id]
        readset_id integer
        name text
        start timestamp
        stop timestamp
        status status
        type text
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "job"

    operation_id: Mapped[int] = mapped_column(ForeignKey("operation.id"), default=None)
    name: Mapped[str] = mapped_column(default=None, nullable=True)
    start: Mapped[datetime] = mapped_column(default=None, nullable=True)
    stop: Mapped[datetime] = mapped_column(default=None, nullable=True)
    status: Mapped[StatusEnum] = mapped_column(default=None, nullable=True)
    type: Mapped[str] = mapped_column(default=None, nullable=True)

    operation: Mapped["Operation"] = relationship(back_populates="jobs")
    metrics: Mapped[list["Metric"]] = relationship(back_populates="job", cascade="all, delete")
    files: Mapped[list["File"]] = relationship(secondary=job_file,back_populates="jobs")
    readsets: Mapped[list["Readset"]] = relationship(secondary=readset_job, back_populates="jobs")


class Metric(BaseTable):
    """
    Metric:
        id integer [PK]
        job_id integer [ref: > job.id]
        name text
        value text
        flag text //pass, warn, fail
        deliverable boolean
        aggregate text //operation to perform for aggregating metric per sample
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "metric"

    name: Mapped[str] = mapped_column(nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("job.id"), default=None)
    value: Mapped[str] = mapped_column(default=None, nullable=True)
    flag: Mapped[FlagEnum] = mapped_column(default=None, nullable=True)
    deliverable: Mapped[bool] = mapped_column(default=False)
    aggregate: Mapped[AggregateEnum] = mapped_column(default=None, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="metrics")
    readsets: Mapped[list["Readset"]] = relationship(secondary=readset_metric, back_populates="metrics")


class Location(BaseTable):
    """
    Uri:
        id integer [PK]
        file_id integer [ref: > file.id]
        uri text
        endpoint text
        deliverable boolean
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "location"

    file_id: Mapped[int] = mapped_column(ForeignKey("file.id"), nullable=False)
    uri: Mapped[str] = mapped_column(nullable=False, unique=True)
    endpoint: Mapped[str] = mapped_column(nullable=False)
    deliverable: Mapped[bool] = mapped_column(default=False)

    file: Mapped["File"] = relationship(back_populates="locations")

    @classmethod
    def from_uri(cls, uri, file, endpoint=None, session=None):
        """
        Sets endpoint from uri
        """
        if not session:
            session = database.get_session()

        location = session.scalars(select(cls).where(cls.uri == uri)).first()
        if not location:
            if endpoint is None:
                endpoint = uri.split(':///')[0]
            location = cls(uri=uri, file=file, endpoint=endpoint)

        return location


class File(BaseTable):
    """
    File:
        id integer [PK]
        name text
        type text
        md5sum txt
        deliverable boolean
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "file"

    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(default=None, nullable=True)
    md5sum: Mapped[str] = mapped_column(default=None, nullable=True)
    deliverable: Mapped[bool] = mapped_column(default=False)

    locations: Mapped[list["Location"]] = relationship(back_populates="file", cascade="all, delete")
    readsets: Mapped[list["Readset"]] = relationship(secondary=readset_file, back_populates="files")
    jobs: Mapped[list["Job"]] = relationship(secondary=job_file, back_populates="files")

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Boolean,
    String,
    JSON,
    DateTime,
    Enum,
    Table
    )
from sqlalchemy.orm import (
    relationship,
    DeclarativeBase,
    Mapped,
    mapped_column
    )

class LaneEnum(enum.Enum):
    """
    lane enum
    """
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"

class SequencingTypeEnum(enum.Enum):
    """
    sequencing_type enum
    """
    SINGLE_END = "SINGLE_END"
    PAIRED_END = "PAIRED_END"

class StatusEnum(enum.Enum):
    """
    status enum
    """
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"

class FlagEnum(enum.Enum):
    """
    flag enum
    """
    PASS = "PASS"
    WARNING = "WARNING"
    FAILED = "FAILED"

class AggregateEnum(enum.Enum):
    """
    aggregate enum
    """
    SUM = "SUM"
    AVERAGE = "AVERAGE"
    N = "N" # for NOT aggregating for metric at sample level

class BaseTable(DeclarativeBase):
    """
    Define fields common of all tables in database
    BaseTable:
        id integer [PK]
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    deprecated: Mapped[bool] = mapped_column(default=False)
    deleted: Mapped[bool] = mapped_column(default=False)
    creation: Mapped[datetime] = mapped_column(default=datetime.now(), nullable=True)
    modification: Mapped[datetime] = mapped_column(default=None, nullable=True)
    extra_metadata: Mapped[dict] = mapped_column(default=None, nullable=True)

class Project(BaseTable):
    """
    Project:
        id integer [PK]
        fms_id integer
        name text (unique)
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "project"

    fms_id: Mapped[str] = mapped_column(default=None, nullable=True)
    name: Mapped[str] = mapped_column(default=None, nullable=False, unique=True)

    patient: Mapped[list["Patient"]] = relationship(back_populates="project")

class Patient(BaseTable):
    """
    Patient:
        id integer [PK]
        project_id integer [ref: > project.id]
        fms_id integer
        name text (unique)
        alias blob
        cohort text
        institution text
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "patient"

    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), default=None)
    fms_id: Mapped[str] = mapped_column(default=None, nullable=True)
    name: Mapped[str] = mapped_column(default=None, nullable=False, unique=True)
    alias: Mapped[str] = mapped_column(default=None, nullable=True)
    cohort: Mapped[str] = mapped_column(default=None, nullable=True)
    institution: Mapped[str] = mapped_column(default=None, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="patient")
    sample: Mapped[list["Sample"]] = relationship(back_populates="patient")

class Sample(BaseTable):
    """
    Sample:
        id integer [PK]
        patient_id integer [ref: > patient.id]
        fms_id integer
        name text
        tumour boolean
        alias blob
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "sample"

    patient_id: Mapped[int] = mapped_column(ForeignKey("patient.id"), default=None)
    fms_id: Mapped[str] = mapped_column(default=None, nullable=True)
    name: Mapped[str] = mapped_column(default=None, nullable=False, unique=True)
    tumour: Mapped[bool] = mapped_column(default=False)
    alias: Mapped[str] = mapped_column(default=None, nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="sample")
    readset: Mapped[list["Readset"]] = relationship(back_populates="sample")

class Experiment(BaseTable):
    """
    Experiment:
        id integer [PK]
        sequencing_technology text
        type text
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
    library_kit: Mapped[str] = mapped_column(default=None, nullable=True)
    kit_expiration_date: Mapped[str] = mapped_column(default=None, nullable=True)

    readset: Mapped[list["Readset"]] = relationship(back_populates="experiment")

class Run(BaseTable):
    """
    Patient:
        id integer [PK]
        fms_id text
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

    fms_id: Mapped[str] = mapped_column(default=None, nullable=True)
    name: Mapped[str] = mapped_column(default=None, nullable=True)
    instrument: Mapped[str] = mapped_column(default=None, nullable=True)
    date: Mapped[datetime] = mapped_column(default=None, nullable=True)

    readset: Mapped[list["Readset"]] = relationship(back_populates="run")

class Readset(BaseTable):
    """
    Readset:
        id integer [PK]
        sample_id integer [ref: > sample.id]
        experiment_id  text [ref: > experiment.id]
        run_id integer [ref: > run.id]
        name text
        lane lane
        adapter1 text
        adapter2 text
        sequencing_type sequencing_type
        quality_offset text
        alias blob
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
    lane: Mapped[Enum(LaneEnum)] = mapped_column(default=None, nullable=True)
    adapter1: Mapped[str] = mapped_column(default=None, nullable=True)
    adapter2: Mapped[str] = mapped_column(default=None, nullable=True)
    sequencing_type: Mapped[Enum(LaneEnum)] = mapped_column(default=None, nullable=True)
    quality_offset: Mapped[str] = mapped_column(default=None, nullable=True)
    alias: Mapped[str] = mapped_column(default=None, nullable=True)

    sample: Mapped["Sample"] = relationship(back_populates="readset")
    experiment: Mapped["Experiment"] = relationship(back_populates="readset")
    run: Mapped["Run"] = relationship(back_populates="readset")
    operation: Mapped[list["Operation"]] = relationship(secondary=readset_operation, back_populates="readset")
    job: Mapped[list["Job"]] = relationship(secondary=readset_job, back_populates="readset")
    metric: Mapped[list["Metric"]] = relationship(secondary=readset_metric, back_populates="readset")

readset_metric = Table(
    "readset_metric",
    DeclarativeBase.metadata,
    Column("readset_id", ForeignKey("readset.id"), primary_key=True),
    Column("metric_id", ForeignKey("metric.id"), primary_key=True),
)

readset_job = Table(
    "readset_job",
    DeclarativeBase.metadata,
    Column("readset_id", ForeignKey("readset.id"), primary_key=True),
    Column("job_id", ForeignKey("job.id"), primary_key=True),
)

readset_operation = Table(
    "readset_operation",
    DeclarativeBase.metadata,
    Column("readset_id", ForeignKey("readset.id"), primary_key=True),
    Column("operation_id", ForeignKey("operation.id"), primary_key=True),
)

class Operation(BaseTable):
    """
    Operation:
        id integer [PK]
        operation_config_id integer [ref: > operation_config.id]
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

    operation_config_id: Mapped[int] = mapped_column(ForeignKey("operation_config.id"), default=None)
    platform: Mapped[str] = mapped_column(default=None, nullable=True)
    cmd_line: Mapped[str] = mapped_column(default=None, nullable=True)
    name: Mapped[str] = mapped_column(default=None, nullable=True)
    status: Mapped[Enum(LaneEnum)] = mapped_column(default=None, nullable=True)

    operation_config: Mapped["OperationConfig"] = relationship(back_populates="operation")
    job: Mapped[list["Job"]] = relationship(back_populates="operation")
    bundle: Mapped[list["Bundle"]] = relationship(secondary=operation_bundle, back_populates="operation")
    readset: Mapped[list["Readset"]] = relationship(secondary=readset_job, back_populates="operation")

operation_bundle = Table(
    "operation_bundle",
    DeclarativeBase.metadata,
    Column("operation_id", ForeignKey("operation.id"), primary_key=True),
    Column("bundle_id", ForeignKey("bundle.id"), primary_key=True),
)

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
    status: Mapped[Enum(LaneEnum)] = mapped_column(default=None, nullable=True)
    type: Mapped[str] = mapped_column(default=None, nullable=True)

    operation: Mapped["Operation"] = relationship(back_populates="job")
    metric: Mapped[list["Metric"]] = relationship(back_populates="job")
    bundle: Mapped[list["Bundle"]] = relationship(back_populates="job")
    readset: Mapped[list["Readset"]] = relationship(secondary=readset_job, back_populates="job")

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

    job_id: Mapped[int] = mapped_column(ForeignKey("job.id"), default=None)
    name: Mapped[str] = mapped_column(default=None, nullable=True)
    value: Mapped[str] = mapped_column(default=None, nullable=True)
    flag: Mapped[Enum(FlagEnum)] = mapped_column(default=None, nullable=True)
    deliverable: Mapped[bool] = mapped_column(default=False)
    aggregate: Mapped[Enum(AggregateEnum)] = mapped_column(default=None, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="metric")
    readset: Mapped[list["Readset"]] = relationship(secondary=readset_metric, back_populates="metric")


class Bundle(BaseTable):
    """
    Bundle:
        id integer [PK]
        job_id integer [ref: > job.id]
        uri text
        deliverable bool
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "bundle"

    job_id: Mapped[int] = mapped_column(ForeignKey("job.id"), default=None)
    uri: Mapped[str] = mapped_column(default=None, nullable=True)
    deliverable: Mapped[bool] = mapped_column(default=False)

    job: Mapped["Job"] = relationship(back_populates="bundle")
    file: Mapped[list["File"]] = relationship(back_populates="bundle")
    operation: Mapped[list["Operation"]] = relationship(secondary=operation_bundle, back_populates="bundle")
    bundle: Mapped[list["Bundle"]] = relationship(secondary=bundle_bundle, back_populates="bundle")

bundle_bundle = Table(
    "bundle_bundle",
    DeclarativeBase.metadata,
    Column("bundle_id", ForeignKey("bundle.id"), primary_key=True),
    Column("reference_id", ForeignKey("bundle.id"), primary_key=True),
)

class File(BaseTable):
    """
    File:
        id integer [PK]
        bundle_id integer [ref: > bundle.id]
        content text
        type text
        deliverable boolean
        deprecated boolean
        deleted boolean
        creation timestamp
        modification timestamp
        extra_metadata json
    """
    __tablename__ = "file"

    bundle_id: Mapped[int] = mapped_column(ForeignKey("bundle.id"), default=None)
    content: Mapped[str] = mapped_column(default=None, nullable=True)
    type: Mapped[str] = mapped_column(default=None, nullable=True)
    deliverable: Mapped[bool] = mapped_column(default=False)

    bundle: Mapped["Bundle"] = relationship(back_populates="file")

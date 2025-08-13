from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = os.getenv("DB_URL")


engine = create_engine(DB_URL,
    pool_pre_ping=True,
    pool_recycle=1800)  

Session = sessionmaker(bind=engine)
Base = declarative_base()

class Transcript(Base):
    __tablename__ = 'transcripts'
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    transcription = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    venue_id = Column(Integer, ForeignKey('venues.id'))
    venue = relationship("Venue")
    day_id = Column(Integer, ForeignKey('days.id'))
    day = relationship("Days")
    summary = relationship("Summary", back_populates="transcript", uselist=False)
    conclusions = relationship("Conclusions", back_populates="transcript", uselist=False)
    theses = relationship("Theses", back_populates="transcript", uselist=False)


class Venue(Base):
    __tablename__ = 'venues'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    transcripts = relationship('Transcript', back_populates='venue')

class Days(Base):
    __tablename__ = 'days'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    transcripts = relationship('Transcript', back_populates='day')

class Summary(Base):
    __tablename__ = 'summary'
    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcripts.id'))
    summary = Column(String, nullable=False, unique=True)

    transcript = relationship("Transcript", back_populates="summary")

class Conclusions(Base):
    __tablename__ = 'conclusions'
    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcripts.id'))
    conclusions = Column(String, nullable=False, unique=True)

    transcript = relationship("Transcript", back_populates="conclusions")

class Theses(Base):
    __tablename__ = 'theses'
    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcripts.id'))
    theses = Column(String, nullable=False, unique=True)

    transcript = relationship("Transcript", back_populates="theses")


    

def init_db():
    Base.metadata.create_all(engine, checkfirst=True)

def insert_transcript(filename, transcription, venue_id, day_id):
    session = Session()
    transcript = Transcript(filename=filename, transcription=transcription, venue_id=venue_id, day_id=day_id)
    session.add(transcript)
    session.commit()
    transcript_id = transcript.id
    session.close()
    return transcript_id
    

def get_all_transcripts():
    session = Session()
    transcripts = session.query(Transcript.filename, Transcript.created_at, Transcript.id).order_by(Transcript.created_at.desc()).all()
    session.close()
    return transcripts

def get_transcript_by_id(transcript_id):
    session = Session()
    transcript = session.query(Transcript).filter_by(id=transcript_id).first()
    session.close()
    return transcript

def get_all_venues():
    session = Session()
    venues = session.query(Venue).all()
    session.close()
    return venues

def get_all_days():
    session = Session()
    days = session.query(Days).all()
    session.close()
    return  days



def get_venue_by_transcript_id(transcript_id):
    session = Session()
    transcript = session.query(Transcript)\
        .options(joinedload(Transcript.venue))\
        .filter_by(id=transcript_id)\
        .first()
    session.close()
    if transcript:
        return transcript.venue
    return None


def get_day_by_transcript_id(transcript_id):
    session = Session()
    transcript = session.query(Transcript)\
        .options(joinedload(Transcript.day))\
        .filter_by(id=transcript_id)\
        .first()
    session.close()
    if transcript:
        return transcript.day
    return None


def get_venue_day_by_id(venue_id,  day_id):
    session = Session()
    venue = session.query(Venue).filter_by(id=venue_id).first()
    day = session.query(Days).filter_by(id=day_id).first()
    session.close()
    return venue, day


def insert_summary(transcript_id, result):
    session = Session()
    summary = Summary(transcript_id=transcript_id, summary=result['summary'])
    session.add(summary)
    for el in result['conclusions']:
        conclusion = Conclusions(transcript_id=transcript_id, conclusions=el)
        session.add(conclusion)
    for el in result['theses']:
        thesis = Theses(transcript_id=transcript_id, theses=el)
        session.add(thesis)
    session.commit()
    session.close()
    return None

def get_transcript_id_by_transcription(transcription_text):

    session = Session()

    transcript = session.query(Transcript)\
        .filter(Transcript.transcription == transcription_text)\
        .first()
    session.close()

    return transcript.id if transcript else None

        
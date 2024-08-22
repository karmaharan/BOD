from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UserLogin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    login_time = db.Column(db.DateTime)
    last_resume_analysis = db.Column(db.DateTime, default=None)
    resume_analysis_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<UserLogin {self.email} - {self.login_time}>"

class ActiveQueue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    queue_rank = db.Column(db.Integer, nullable=False)
    total_queue = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<ActiveQueue {self.email} - Rank: {self.queue_rank} of {self.total_queue}>"

    @staticmethod
    def add_to_queue(email, name):
        total_queue = ActiveQueue.query.count() + 1
        new_queue_entry = ActiveQueue(email=email, name=name, queue_rank=total_queue, total_queue=total_queue)
        db.session.add(new_queue_entry)
        db.session.commit()

    @staticmethod
    def remove_from_queue(email):
        queue_entry = ActiveQueue.query.filter_by(email=email).first()
        if queue_entry:
            db.session.delete(queue_entry)
            db.session.commit()
            # Update the queue ranks for remaining users
            remaining_entries = ActiveQueue.query.order_by(ActiveQueue.queue_rank).all()
            for index, entry in enumerate(remaining_entries):
                entry.queue_rank = index + 1
                entry.total_queue = len(remaining_entries)
            db.session.commit()

    @staticmethod
    def get_next_in_queue():
        return ActiveQueue.query.order_by(ActiveQueue.queue_rank).first()

from flask import Flask, redirect, render_template, request, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from datetime import timezone

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

db = SQLAlchemy(app)

# Jinja filter: convert stored datetimes (assumed UTC if naive) to local timezone and format
def to_local_time(dt):
    if not dt:
        return ''
    try:
        # if datetime has no tzinfo, assume it's UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # astimezone() with no argument converts to the system local timezone
        local_dt = dt.astimezone()
        return local_dt.strftime('%b %d, %Y %I:%M %p')
    except Exception:
        # fallback to a safe string
        try:
            return dt.strftime('%b %d, %Y %I:%M %p')
        except Exception:
            return str(dt)

app.jinja_env.filters['localtime'] = to_local_time

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_content = request.form.get('content', '').strip()
        if not task_content:
            flash('Task content cannot be empty.', 'error')
            return redirect(url_for('index'))
        new_task = Todo(content=task_content)
        try:
            db.session.add(new_task)
            db.session.commit()
            flash('Task added successfully.', 'success')
            return redirect(url_for('index'))
        except Exception:
            flash('There was an issue adding your task. Please try again.', 'error')
            return redirect(url_for('index'))
    else:
        tasks = (
            Todo.query.order_by(Todo.completed.asc(), Todo.date_created.desc()).all()
        )
        return render_template('index.html', tasks=tasks)
       
@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        flash('Task deleted.', 'success')
        return redirect(url_for('index'))
    except Exception:
        flash('There was a problem deleting that task.', 'error')
        return redirect(url_for('index'))
    
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)
    if request.method == 'POST':
        new_content = request.form.get('content', '').strip()
        if not new_content:
            flash('Task content cannot be empty.', 'error')
            return render_template('update.html', task=task)
        task.content = new_content
        try:
            db.session.commit()
            flash('Task updated.', 'success')
            return redirect(url_for('index'))
        except Exception:
            flash('There was an issue updating your task.', 'error')
            return render_template('update.html', task=task)
    else:
        return render_template('update.html', task=task)    

@app.route('/toggle/<int:id>')
def toggle(id):
    task = Todo.query.get_or_404(id)
    try:
        task.completed = 0 if task.completed else 1
        db.session.commit()
        flash('Task status updated.', 'success')
    except Exception:
        flash('Unable to update task status.', 'error')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)

from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Equipment

equipment = Blueprint('equipment', __name__, url_prefix='/equipment')

@equipment.route('/')
@login_required
def list_equipment():
    equipment_list = Equipment.query.all()
    return render_template('equipment_list.html', equipment=equipment_list)

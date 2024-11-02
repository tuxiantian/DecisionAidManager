import json
from flask import Flask, request, jsonify, Blueprint
from shared_models import BalancedDecision, db
from datetime import datetime as dt
from flask_login import current_user

balanced_decision_bp = Blueprint('balanced_decision', __name__)
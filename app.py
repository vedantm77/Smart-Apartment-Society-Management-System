"""
Smart Society Management System - COMPLETE with ALL DSA
Includes: Linked List, Queue, Stack, Heap, Graph, Tree, Search, Sort
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import json
import os
from datetime import datetime
from functools import wraps

# Import DSA structures
from dsa_structures.linked_list import LinkedList
from dsa_structures.heap import MinHeap
from dsa_structures.queue import Queue
from dsa_structures.stack import Stack
from dsa_structures.graph import Graph
from dsa_structures.tree import SocietyTree  # NEW

# Import services
from services.resident_service import ResidentService
from services.complaint_service import ComplaintService
from services.visitor_service import VisitorService

app = Flask(__name__)
CORS(app)
app.secret_key = 'society-management-secret-key-2024'

# Configuration
app.config['DEBUG'] = True
app.config['JSON_SORT_KEYS'] = False

# Data directory
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize services
resident_service = ResidentService(DATA_DIR)
complaint_service = ComplaintService(DATA_DIR)
visitor_service = VisitorService(DATA_DIR)

# Initialize Tree for building structure
society_tree = SocietyTree("Green Valley Apartments")

# Initialize sample building structure
def initialize_building_structure():
    """Create Tower → Floor → Flat hierarchy"""
    # Tower A
    tower_a = society_tree.add_tower("Tower A")
    for floor_num in range(1, 4):  # 3 floors
        floor = society_tree.add_floor(tower_a, floor_num)
        for flat_num in range(1, 3):  # 2 flats per floor
            flat_number = f"A-{floor_num}0{flat_num}"
            society_tree.add_flat(floor, flat_number)
    
    # Tower B
    tower_b = society_tree.add_tower("Tower B")
    for floor_num in range(1, 4):
        floor = society_tree.add_floor(tower_b, floor_num)
        for flat_num in range(1, 3):
            flat_number = f"B-{floor_num}0{flat_num}"
            society_tree.add_flat(floor, flat_number)

# Initialize Graph for facilities
facility_graph = Graph()
facilities = ['🏊 Swimming Pool', '🏋️ Gym', '🅿️ Parking', '🌳 Garden', '🎾 Tennis Court', '👶 Kids Play Area']
for facility in facilities:
    facility_graph.add_vertex(facility)

facility_graph.add_edge('🏊 Swimming Pool', '🏋️ Gym')
facility_graph.add_edge('🏊 Swimming Pool', '🌳 Garden')
facility_graph.add_edge('🏋️ Gym', '🅿️ Parking')
facility_graph.add_edge('🌳 Garden', '👶 Kids Play Area')
facility_graph.add_edge('🌳 Garden', '🎾 Tennis Court')
facility_graph.add_edge('🅿️ Parking', '🎾 Tennis Court')

# Users (Admin + Residents)
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin', 'name': 'System Admin'},
    'resident1': {'password': 'pass123', 'role': 'resident', 'name': 'Rajesh Kumar', 'flat': 'A-101'},
    'resident2': {'password': 'pass123', 'role': 'resident', 'name': 'Priya Sharma', 'flat': 'A-102'}
}


# ==================== DECORATORS ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ==================== AUTH ROUTES ====================

@app.route('/')
def login_page():
    if 'user' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('resident_dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = USERS.get(username)
    if user and user['password'] == password:
        session['user'] = username
        session['role'] = user['role']
        session['name'] = user['name']
        if user['role'] == 'resident':
            session['flat'] = user.get('flat')
        
        return jsonify({'success': True, 'role': user['role'], 'name': user['name']})
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if session['role'] != 'admin':
        return redirect(url_for('resident_dashboard'))
    
    stats = {
        'total_residents': resident_service.get_count(),
        'total_visitors': visitor_service.get_count(),
        'active_complaints': complaint_service.get_count(),
        'total_billing': resident_service.get_total_billing(),
        'total_flats': society_tree.get_total_flats()
    }
    return render_template('admin_dashboard.html', stats=stats, user=session['name'])


@app.route('/admin/residents')
@login_required
def admin_residents():
    if session['role'] != 'admin':
        return redirect(url_for('resident_dashboard'))
    return render_template('admin_residents.html', user=session['name'])


@app.route('/admin/visitors')
@login_required
def admin_visitors():
    if session['role'] != 'admin':
        return redirect(url_for('resident_dashboard'))
    return render_template('admin_visitors.html', user=session['name'])


@app.route('/admin/complaints')
@login_required
def admin_complaints():
    if session['role'] != 'admin':
        return redirect(url_for('resident_dashboard'))
    return render_template('admin_complaints.html', user=session['name'])


@app.route('/admin/bills')
@login_required
def admin_bills():
    if session['role'] != 'admin':
        return redirect(url_for('resident_dashboard'))
    return render_template('admin_bills.html', user=session['name'])


# ==================== RESIDENT ROUTES ====================

@app.route('/resident/dashboard')
@login_required
def resident_dashboard():
    if session['role'] != 'resident':
        return redirect(url_for('admin_dashboard'))
    
    flat = session.get('flat')
    stats = {
        'flat_number': flat,
        'pending_bills': 1,
        'active_complaints': 2,
        'visitors_today': visitor_service.get_count()
    }
    return render_template('resident_dashboard.html', stats=stats, user=session['name'])


@app.route('/resident/complaints')
@login_required
def resident_complaints():
    if session['role'] != 'resident':
        return redirect(url_for('admin_dashboard'))
    return render_template('resident_complaints.html', user=session['name'], flat=session.get('flat'))


@app.route('/resident/bills')
@login_required
def resident_bills():
    if session['role'] != 'resident':
        return redirect(url_for('admin_dashboard'))
    return render_template('resident_bills.html', user=session['name'], flat=session.get('flat'))


@app.route('/resident/visitors')
@login_required
def resident_visitors():
    if session['role'] != 'resident':
        return redirect(url_for('admin_dashboard'))
    return render_template('resident_visitors.html', user=session['name'], flat=session.get('flat'))


# ==================== API ENDPOINTS ====================

# RESIDENT APIs
@app.route('/api/residents', methods=['GET'])
@login_required
def get_residents():
    residents = resident_service.get_all()
    return jsonify({'success': True, 'data': residents, 'count': len(residents)})


@app.route('/api/residents/search/<flat_number>', methods=['GET'])
@login_required
def search_resident(flat_number):
    """Binary Search for resident by flat number"""
    resident = resident_service.search_by_flat(flat_number)
    if resident:
        return jsonify({'success': True, 'data': resident})
    return jsonify({'success': False, 'message': 'Resident not found'}), 404


@app.route('/api/residents/sort', methods=['GET'])
@login_required
def sort_residents():
    """Sort residents by pending bills using Quick Sort"""
    sort_by = request.args.get('by', 'name')  # name, flat, bills
    residents = resident_service.sort_residents(sort_by)
    return jsonify({'success': True, 'data': residents})


@app.route('/api/residents', methods=['POST'])
@login_required
@admin_required
def add_resident():
    data = request.json
    required_fields = ['name', 'flat', 'phone', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    resident_service.add_resident(data)
    return jsonify({'success': True, 'message': 'Resident added', 'data': data}), 201


@app.route('/api/residents/<flat_number>', methods=['DELETE'])
@login_required
@admin_required
def delete_resident(flat_number):
    success = resident_service.delete_resident(flat_number)
    if success:
        return jsonify({'success': True, 'message': f'Resident deleted'})
    return jsonify({'success': False, 'message': 'Resident not found'}), 404


# TREE API (Building Structure)
@app.route('/api/building/structure', methods=['GET'])
@login_required
def get_building_structure():
    """Get Tower → Floor → Flat hierarchy"""
    towers = society_tree.get_all_towers()
    structure = []
    for tower in towers:
        structure.append(society_tree.get_tower_structure(tower))
    return jsonify({'success': True, 'data': structure})


@app.route('/api/building/search/<flat_number>', methods=['GET'])
@login_required
def search_flat_location(flat_number):
    """Search flat location in building tree"""
    result = society_tree.search_flat(flat_number)
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'message': 'Flat not found'}), 404


# VISITOR APIs
@app.route('/api/visitors', methods=['GET'])
@login_required
def get_visitors():
    visitors = visitor_service.get_all()
    return jsonify({'success': True, 'data': visitors, 'count': len(visitors)})


@app.route('/api/visitors', methods=['POST'])
@login_required
def add_visitor():
    data = request.json
    required_fields = ['name', 'flat', 'purpose']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
    
    data['time'] = datetime.now().strftime('%H:%M:%S')
    visitor_service.enqueue_visitor(data)
    return jsonify({'success': True, 'message': 'Visitor added', 'data': data}), 201


@app.route('/api/visitors/process', methods=['POST'])
@login_required
@admin_required
def process_visitor():
    visitor = visitor_service.dequeue_visitor()
    if visitor:
        return jsonify({'success': True, 'message': 'Visitor processed', 'data': visitor})
    return jsonify({'success': False, 'message': 'No visitors in queue'}), 404


# COMPLAINT APIs
@app.route('/api/complaints', methods=['GET'])
@login_required
def get_complaints():
    complaints = complaint_service.get_all()
    if session['role'] == 'resident':
        flat = session.get('flat')
        complaints = [c for c in complaints if c.get('flat') == flat]
    return jsonify({'success': True, 'data': complaints, 'count': len(complaints)})


@app.route('/api/complaints', methods=['POST'])
@login_required
def add_complaint():
    data = request.json
    required_fields = ['title', 'flat', 'priority', 'desc']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
    
    data['priority'] = int(data['priority'])
    data['time'] = datetime.now().strftime('%H:%M:%S')
    complaint_service.add_complaint(data)
    return jsonify({'success': True, 'message': 'Complaint submitted', 'data': data}), 201


@app.route('/api/complaints/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_complaint():
    complaint = complaint_service.resolve_complaint()
    if complaint:
        return jsonify({'success': True, 'message': 'Complaint resolved', 'data': complaint})
    return jsonify({'success': False, 'message': 'No complaints'}), 404


# BILLING APIs
@app.route('/api/bills', methods=['GET'])
@login_required
def get_bills():
    bills = resident_service.get_all_bills()
    if session['role'] == 'resident':
        flat = session.get('flat')
        bills = [b for b in bills if b.get('flat') == flat]
    return jsonify({'success': True, 'data': bills, 'count': len(bills)})


@app.route('/api/bills', methods=['POST'])
@login_required
@admin_required
def add_bill():
    data = request.json
    required_fields = ['flat', 'amount', 'desc']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
    
    data['amount'] = int(data['amount'])
    data['date'] = datetime.now().strftime('%Y-%m-%d')
    resident_service.add_bill(data)
    return jsonify({'success': True, 'message': 'Bill added', 'data': data}), 201


@app.route('/api/bills/undo', methods=['POST'])
@login_required
@admin_required
def undo_bill():
    bill = resident_service.undo_bill()
    if bill:
        return jsonify({'success': True, 'message': 'Bill undone', 'data': bill})
    return jsonify({'success': False, 'message': 'No bills to undo'}), 404


# FACILITY APIs
@app.route('/api/facilities', methods=['GET'])
@login_required
def get_facilities():
    vertices = facility_graph.get_vertices()
    connections = {}
    for vertex in vertices:
        connections[vertex] = facility_graph.get_connections(vertex)
    return jsonify({'success': True, 'data': {'facilities': vertices, 'connections': connections}})


# DASHBOARD API
@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    return jsonify({
        'success': True,
        'data': {
            'total_residents': resident_service.get_count(),
            'total_visitors': visitor_service.get_count(),
            'active_complaints': complaint_service.get_count(),
            'total_billing': resident_service.get_total_billing(),
            'total_flats': society_tree.get_total_flats()
        }
    })


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'Server error'}), 500


# ==================== RUN ====================

if __name__ == '__main__':
    # Initialize data
    resident_service.initialize_sample_data()
    visitor_service.initialize_sample_data()
    complaint_service.initialize_sample_data()
    initialize_building_structure()
    
    print("=" * 70)
    print("🏢 SMART SOCIETY MANAGEMENT SYSTEM - ALL DSA INTEGRATED")
    print("=" * 70)
    print("✅ Linked List - Resident Management")
    print("✅ Queue (FIFO) - Visitor Entry")
    print("✅ Stack (LIFO) - Billing Undo")
    print("✅ Min Heap - Priority Complaints")
    print("✅ Graph - Facility Connections")
    print("✅ Tree - Tower → Floor → Flat Hierarchy")
    print("✅ Binary Search - Search by Flat Number")
    print("✅ Quick Sort - Sort Residents by Bills")
    print("=" * 70)
    print("🌐 Server: http://localhost:5000")
    print("=" * 70)
    print("👤 CREDENTIALS:")
    print("   Admin    → admin / admin123")
    print("   Resident → resident1 / pass123")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

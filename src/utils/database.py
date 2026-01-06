"""
Shared Database Utility for Analytics Engine
=============================================

Provides database connection and query utilities using the centralized database.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# Shared database path
DB_PATH = Path(__file__).parent.parent.parent.parent / "database" / "logistics.db"

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def dict_from_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert sqlite3.Row to dictionary"""
    return dict(zip(row.keys(), row))

def query_shipments(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Query shipments with optional filters"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM shipments"
        params = []
        
        if filters:
            conditions = []
            if 'job_number' in filters:
                conditions.append("job_number = ?")
                params.append(filters['job_number'])
            if 'status' in filters:
                conditions.append("status = ?")
                params.append(filters['status'])
            if 'container_number' in filters:
                conditions.append("container_number = ?")
                params.append(filters['container_number'])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]

def query_transport_legs(shipment_id: int) -> List[Dict[str, Any]]:
    """Query transport legs for a shipment"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM transport_legs 
            WHERE shipment_id = ? 
            ORDER BY leg_number
        """, (shipment_id,))
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]

def query_vessel_positions(vessel_name: Optional[str] = None, 
                          imo_number: Optional[str] = None) -> List[Dict[str, Any]]:
    """Query vessel positions"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM vessel_positions"
        params = []
        conditions = []
        
        if vessel_name:
            conditions.append("vessel_name LIKE ?")
            params.append(f"%{vessel_name}%")
        if imo_number:
            conditions.append("imo_number = ?")
            params.append(imo_number)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp DESC LIMIT 10"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]

def query_container_sensors(container_number: str) -> List[Dict[str, Any]]:
    """Query container sensor data"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM container_sensors 
            WHERE container_number = ? 
            ORDER BY timestamp DESC 
            LIMIT 100
        """, (container_number,))
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]

def insert_vessel_position(data: Dict[str, Any]) -> int:
    """Insert new vessel position record"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vessel_positions 
            (vessel_name, imo_number, mmsi, latitude, longitude, speed, 
             heading, status, next_port, eta, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['vessel_name'], data.get('imo_number'), data.get('mmsi'),
            data['latitude'], data['longitude'], data.get('speed'),
            data.get('heading'), data.get('status'), data.get('next_port'),
            data.get('eta'), data['timestamp']
        ))
        conn.commit()
        return cursor.lastrowid

def insert_container_sensor(data: Dict[str, Any]) -> int:
    """Insert new container sensor record"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO container_sensors 
            (container_number, latitude, longitude, temperature, humidity,
             shock_detected, door_opened, battery_level, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['container_number'], data.get('latitude'), data.get('longitude'),
            data.get('temperature'), data.get('humidity'), data.get('shock_detected', 0),
            data.get('door_opened', 0), data.get('battery_level'), 
            data.get('status'), data['timestamp']
        ))
        conn.commit()
        return cursor.lastrowid

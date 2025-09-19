"""
Database manager for API data persistence.
Uses SQLite for development and can be extended for production databases.
"""
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import asyncio
import aiosqlite

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for the API."""
    
    def __init__(self, db_path: str = "contract_api.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Contracts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS contracts (
                        contract_id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        status TEXT DEFAULT 'uploaded',
                        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processing_started TIMESTAMP,
                        processing_completed TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_size INTEGER DEFAULT 0,
                        use_layoutlm BOOLEAN DEFAULT FALSE,
                        processing_result TEXT,
                        message TEXT
                    )
                """)
                
                # Contract sections table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS contract_sections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contract_id TEXT NOT NULL,
                        section_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        section_type TEXT,
                        importance_score REAL,
                        clause_count INTEGER DEFAULT 0,
                        contains_obligations BOOLEAN DEFAULT FALSE,
                        contains_conditions BOOLEAN DEFAULT FALSE,
                        text TEXT,
                        metadata TEXT,
                        FOREIGN KEY (contract_id) REFERENCES contracts (contract_id)
                    )
                """)
                
                # Contract clauses table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS contract_clauses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contract_id TEXT NOT NULL,
                        clause_id TEXT NOT NULL,
                        section_id TEXT,
                        text TEXT NOT NULL,
                        legal_category TEXT,
                        risk_level TEXT,
                        confidence_score REAL,
                        key_terms TEXT,
                        obligations TEXT,
                        conditions TEXT,
                        metadata TEXT,
                        FOREIGN KEY (contract_id) REFERENCES contracts (contract_id)
                    )
                """)
                
                # Contract analysis table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS contract_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contract_id TEXT NOT NULL,
                        summary TEXT,
                        key_terms TEXT,
                        risk_assessment TEXT,
                        contract_type TEXT,
                        jurisdiction TEXT,
                        compliance_flags TEXT,
                        missing_clauses TEXT,
                        unusual_terms TEXT,
                        analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (contract_id) REFERENCES contracts (contract_id)
                    )
                """)
                
                # Batch jobs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_jobs (
                        batch_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        contract_ids TEXT NOT NULL,
                        total_contracts INTEGER NOT NULL,
                        completed_contracts INTEGER DEFAULT 0,
                        failed_contracts INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'started',
                        progress INTEGER DEFAULT 0,
                        options TEXT,
                        results TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        error TEXT
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_user_id ON contracts (user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts (status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_clauses_contract_id ON contract_clauses (contract_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sections_contract_id ON contract_sections (contract_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_jobs_user_id ON batch_jobs (user_id)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
    
    def check_connection(self) -> bool:
        """Check database connection."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    # Contract operations
    
    async def create_contract(self, contract_data: Dict[str, Any]):
        """Create a new contract record."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO contracts (
                    contract_id, filename, file_path, user_id, status,
                    upload_date, file_size, use_layoutlm
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract_data["contract_id"],
                contract_data["filename"],
                contract_data["file_path"],
                contract_data["user_id"],
                contract_data["status"],
                contract_data["upload_date"],
                contract_data["file_size"],
                contract_data["use_layoutlm"]
            ))
            await db.commit()
    
    async def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get contract by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM contracts WHERE contract_id = ?",
                (contract_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                contract = dict(row)
                if contract["processing_result"]:
                    contract["processing_result"] = json.loads(contract["processing_result"])
                return contract
            return None
    
    async def update_contract(self, contract_id: str, update_data: Dict[str, Any]):
        """Update contract record."""
        set_clauses = []
        values = []
        
        for key, value in update_data.items():
            if key == "processing_result" and value:
                value = json.dumps(value, default=str)
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(contract_id)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE contracts SET {', '.join(set_clauses)} WHERE contract_id = ?",
                values
            )
            await db.commit()
    
    async def delete_contract(self, contract_id: str):
        """Delete contract and related data."""
        async with aiosqlite.connect(self.db_path) as db:
            # Delete related data first
            await db.execute("DELETE FROM contract_analysis WHERE contract_id = ?", (contract_id,))
            await db.execute("DELETE FROM contract_clauses WHERE contract_id = ?", (contract_id,))
            await db.execute("DELETE FROM contract_sections WHERE contract_id = ?", (contract_id,))
            await db.execute("DELETE FROM contracts WHERE contract_id = ?", (contract_id,))
            await db.commit()
    
    async def list_user_contracts(
        self, 
        user_id: str, 
        limit: int, 
        offset: int,
        status: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List user's contracts with pagination."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Build query
            where_clause = "WHERE user_id = ?"
            params = [user_id]
            
            if status:
                where_clause += " AND status = ?"
                params.append(status)
            
            # Get total count
            cursor = await db.execute(
                f"SELECT COUNT(*) FROM contracts {where_clause}",
                params
            )
            total = (await cursor.fetchone())[0]
            
            # Get contracts
            cursor = await db.execute(f"""
                SELECT contract_id, filename, status, upload_date, processing_completed,
                       file_size, processing_result
                FROM contracts {where_clause}
                ORDER BY upload_date DESC
                LIMIT ? OFFSET ?
            """, params + [limit, offset])
            
            rows = await cursor.fetchall()
            contracts = []
            
            for row in rows:
                contract = dict(row)
                
                # Extract additional info from processing result
                if contract["processing_result"]:
                    try:
                        result = json.loads(contract["processing_result"])
                        contract_data = result.get("contract", {})
                        metadata = contract_data.get("metadata", {})
                        contract["pages"] = metadata.get("pages", 0)
                        contract["risk_level"] = self._calculate_overall_risk(contract_data.get("clauses", []))
                        contract["contract_type"] = result.get("analysis", {}).get("contract_type")
                    except:
                        contract["pages"] = 0
                        contract["risk_level"] = None
                        contract["contract_type"] = None
                else:
                    contract["pages"] = 0
                    contract["risk_level"] = None
                    contract["contract_type"] = None
                
                contracts.append(contract)
            
            return contracts, total
    
    def _calculate_overall_risk(self, clauses: List[Dict[str, Any]]) -> Optional[str]:
        """Calculate overall risk level from clauses."""
        if not clauses:
            return None
        
        risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for clause in clauses:
            risk_level = clause.get("risk_level", "low")
            risk_counts[risk_level] += 1
        
        total = sum(risk_counts.values())
        if total == 0:
            return "low"
        
        risk_score = (
            risk_counts["medium"] * 0.3 + 
            risk_counts["high"] * 0.7 + 
            risk_counts["critical"] * 1.0
        ) / total
        
        if risk_score >= 0.7:
            return "critical"
        elif risk_score >= 0.5:
            return "high"
        elif risk_score >= 0.3:
            return "medium"
        else:
            return "low"
    
    # Contract sections operations
    
    async def store_contract_sections(self, contract_id: str, sections: List[Any]):
        """Store contract sections."""
        async with aiosqlite.connect(self.db_path) as db:
            for section in sections:
                await db.execute("""
                    INSERT INTO contract_sections (
                        contract_id, section_id, title, section_type, importance_score,
                        clause_count, contains_obligations, contains_conditions, text, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contract_id,
                    section.id,
                    section.title,
                    getattr(section, 'section_type', None),
                    getattr(section, 'importance_score', None),
                    len(section.clauses),
                    getattr(section, 'contains_obligations', False),
                    getattr(section, 'contains_conditions', False),
                    section.text,
                    json.dumps(getattr(section, 'metadata', {}))
                ))
            await db.commit()
    
    async def get_contract_sections(self, contract_id: str) -> List[Dict[str, Any]]:
        """Get contract sections."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM contract_sections WHERE contract_id = ? ORDER BY id",
                (contract_id,)
            )
            rows = await cursor.fetchall()
            
            sections = []
            for row in rows:
                section = dict(row)
                if section["metadata"]:
                    section["metadata"] = json.loads(section["metadata"])
                sections.append(section)
            
            return sections
    
    # Contract clauses operations
    
    async def store_contract_clauses(self, contract_id: str, clauses: List[Any]):
        """Store contract clauses."""
        async with aiosqlite.connect(self.db_path) as db:
            for clause in clauses:
                await db.execute("""
                    INSERT INTO contract_clauses (
                        contract_id, clause_id, section_id, text, legal_category,
                        risk_level, confidence_score, key_terms, obligations, conditions, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contract_id,
                    clause.id,
                    clause.section,
                    clause.text,
                    clause.legal_category,
                    clause.risk_level,
                    clause.confidence_score,
                    json.dumps(clause.key_terms or []),
                    json.dumps(clause.obligations or []),
                    json.dumps(clause.conditions or []),
                    json.dumps(getattr(clause, 'metadata', {}))
                ))
            await db.commit()
    
    async def get_contract_clauses(self, contract_id: str) -> List[Dict[str, Any]]:
        """Get contract clauses."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM contract_clauses WHERE contract_id = ? ORDER BY id",
                (contract_id,)
            )
            rows = await cursor.fetchall()
            
            clauses = []
            for row in rows:
                clause = dict(row)
                # Parse JSON fields
                for field in ["key_terms", "obligations", "conditions", "metadata"]:
                    if clause[field]:
                        clause[field] = json.loads(clause[field])
                clauses.append(clause)
            
            return clauses
    
    async def get_contract_by_clause(self, clause_id: str) -> Optional[Dict[str, Any]]:
        """Get contract info by clause ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT c.contract_id, c.filename, c.user_id
                FROM contracts c
                JOIN contract_clauses cc ON c.contract_id = cc.contract_id
                WHERE cc.clause_id = ?
            """, (clause_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    # Contract analysis operations
    
    async def store_contract_analysis(self, contract_id: str, analysis: Dict[str, Any]):
        """Store contract analysis."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO contract_analysis (
                    contract_id, summary, key_terms, risk_assessment, contract_type,
                    jurisdiction, compliance_flags, missing_clauses, unusual_terms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract_id,
                analysis.get("summary", ""),
                json.dumps(analysis.get("key_terms", {})),
                json.dumps(analysis.get("risk_assessment", {})),
                analysis.get("contract_type"),
                analysis.get("jurisdiction"),
                json.dumps(analysis.get("compliance_flags", [])),
                json.dumps(analysis.get("missing_clauses", [])),
                json.dumps(analysis.get("unusual_terms", []))
            ))
            await db.commit()
    
    async def get_contract_analysis(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get contract analysis."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM contract_analysis WHERE contract_id = ?",
                (contract_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                analysis = dict(row)
                # Parse JSON fields
                for field in ["key_terms", "risk_assessment", "compliance_flags", "missing_clauses", "unusual_terms"]:
                    if analysis[field]:
                        analysis[field] = json.loads(analysis[field])
                return analysis
            return None
    
    # Batch job operations
    
    async def create_batch_job(self, batch_data: Dict[str, Any]):
        """Create batch job record."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO batch_jobs (
                    batch_id, user_id, contract_ids, total_contracts, status, options, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                batch_data["batch_id"],
                batch_data["user_id"],
                json.dumps(batch_data["contract_ids"]),
                batch_data["total_contracts"],
                batch_data["status"],
                json.dumps(batch_data["options"]),
                batch_data["created_at"]
            ))
            await db.commit()
    
    async def get_batch_job(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch job by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM batch_jobs WHERE batch_id = ?",
                (batch_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                batch = dict(row)
                # Parse JSON fields
                for field in ["contract_ids", "options", "results"]:
                    if batch[field]:
                        batch[field] = json.loads(batch[field])
                return batch
            return None
    
    async def update_batch_job(self, batch_id: str, update_data: Dict[str, Any]):
        """Update batch job."""
        set_clauses = []
        values = []
        
        for key, value in update_data.items():
            if key in ["options", "results"] and value:
                value = json.dumps(value, default=str)
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(batch_id)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE batch_jobs SET {', '.join(set_clauses)} WHERE batch_id = ?",
                values
            )
            await db.commit()
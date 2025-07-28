"""
Citation Analysis and Visualization Module
Provides advanced citation analytics and network visualization
"""

import sqlite3
import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class CitationAnalyzer:
    """Advanced citation analysis and metrics"""
    
    def __init__(self, db_path: str):
        """Initialize citation analyzer"""
        self.db_path = db_path
    
    def calculate_h_index(self, professor_id: int) -> int:
        """
        Calculate H-index for a professor
        
        Args:
            professor_id (int): Professor ID
            
        Returns:
            int: H-index value
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get citation counts for professor's publications
            cursor.execute("""
                SELECT pm.total_citations
                FROM publication_metrics pm
                JOIN author_publications ap ON pm.pmid = ap.publication_pmid
                WHERE ap.professor_id = ?
                ORDER BY pm.total_citations DESC
            """, (professor_id,))
            
            citation_counts = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not citation_counts:
                return 0
            
            # Calculate H-index
            h_index = 0
            for i, citations in enumerate(citation_counts, 1):
                if citations >= i:
                    h_index = i
                else:
                    break
            
            return h_index
            
        except Exception as e:
            logger.error(f"Error calculating H-index: {str(e)}")
            return 0
    
    def calculate_citation_metrics(self, professor_id: int) -> Dict:
        """
        Calculate comprehensive citation metrics for a professor
        
        Args:
            professor_id (int): Professor ID
            
        Returns:
            Dict: Citation metrics including h-index, total citations, etc.
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get publication and citation data
            cursor.execute("""
                SELECT 
                    p.publication_year,
                    COALESCE(pm.total_citations, 0) as citations
                FROM publications p
                JOIN author_publications ap ON p.pmid = ap.publication_pmid
                LEFT JOIN publication_metrics pm ON p.pmid = pm.pmid
                WHERE ap.professor_id = ?
                ORDER BY p.publication_year DESC
            """, (professor_id,))
            
            publications = cursor.fetchall()
            conn.close()
            
            if not publications:
                return {
                    'total_publications': 0,
                    'total_citations': 0,
                    'h_index': 0,
                    'i10_index': 0,
                    'average_citations': 0.0,
                    'citation_velocity': 0.0,
                    'years_active': 0,
                    'publications_by_year': {},
                    'citations_by_year': {}
                }
            
            # Calculate metrics
            citation_counts = [pub[1] for pub in publications]
            years = [pub[0] for pub in publications if pub[0]]
            
            total_publications = len(publications)
            total_citations = sum(citation_counts)
            h_index = self.calculate_h_index(professor_id)
            i10_index = len([c for c in citation_counts if c >= 10])
            average_citations = total_citations / total_publications if total_publications > 0 else 0
            
            # Calculate years active
            years_active = max(years) - min(years) + 1 if years else 0
            
            # Citation velocity (citations per year)
            citation_velocity = total_citations / years_active if years_active > 0 else 0
            
            # Publications and citations by year
            publications_by_year = Counter(years)
            citations_by_year = defaultdict(int)
            
            for pub in publications:
                year, citations = pub[0], pub[1]
                if year:
                    citations_by_year[year] += citations
            
            return {
                'total_publications': total_publications,
                'total_citations': total_citations,
                'h_index': h_index,
                'i10_index': i10_index,
                'average_citations': round(average_citations, 2),
                'citation_velocity': round(citation_velocity, 2),
                'years_active': years_active,
                'publications_by_year': dict(publications_by_year),
                'citations_by_year': dict(citations_by_year)
            }
            
        except Exception as e:
            logger.error(f"Error calculating citation metrics: {str(e)}")
            return {}
    
    def get_top_cited_papers(self, professor_id: int, limit: int = 10) -> List[Dict]:
        """
        Get top cited papers for a professor
        
        Args:
            professor_id (int): Professor ID
            limit (int): Number of top papers to return
            
        Returns:
            List[Dict]: Top cited papers with metadata
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.pmid,
                    p.title,
                    p.journal_name,
                    p.publication_year,
                    COALESCE(pm.total_citations, 0) as citations
                FROM publications p
                JOIN author_publications ap ON p.pmid = ap.publication_pmid
                LEFT JOIN publication_metrics pm ON p.pmid = pm.pmid
                WHERE ap.professor_id = ?
                ORDER BY citations DESC, p.publication_year DESC
                LIMIT ?
            """, (professor_id, limit))
            
            papers = []
            for row in cursor.fetchall():
                papers.append({
                    'pmid': row[0],
                    'title': row[1],
                    'journal': row[2],
                    'year': row[3],
                    'citations': row[4]
                })
            
            conn.close()
            return papers
            
        except Exception as e:
            logger.error(f"Error getting top cited papers: {str(e)}")
            return []
    
    def get_collaboration_network(self, professor_id: int) -> Dict:
        """
        Get collaboration network based on co-authorship and citations
        
        Args:
            professor_id (int): Professor ID
            
        Returns:
            Dict: Collaboration network data
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get co-authors
            cursor.execute("""
                SELECT DISTINCT
                    p2.id,
                    p2.name,
                    p2.university_id,
                    COUNT(*) as collaborations
                FROM author_publications ap1
                JOIN author_publications ap2 ON ap1.publication_pmid = ap2.publication_pmid
                JOIN professors p2 ON ap2.professor_id = p2.id
                WHERE ap1.professor_id = ? AND ap2.professor_id != ?
                GROUP BY p2.id, p2.name, p2.university_id
                ORDER BY collaborations DESC
            """, (professor_id, professor_id))
            
            coauthors = cursor.fetchall()
            
            # Get citation relationships
            cursor.execute("""
                SELECT 
                    cn.cited_professor_id as collaborator_id,
                    p.name as collaborator_name,
                    COUNT(*) as citation_count
                FROM citation_networks cn
                JOIN professors p ON cn.cited_professor_id = p.id
                WHERE cn.citing_professor_id = ?
                GROUP BY cn.cited_professor_id, p.name
                ORDER BY citation_count DESC
            """, (professor_id,))
            
            cited_colleagues = cursor.fetchall()
            
            conn.close()
            
            # Build network
            nodes = []
            edges = []
            
            # Add central professor
            cursor = sqlite3.connect(self.db_path).cursor()
            cursor.execute("SELECT name, university_id FROM professors WHERE id = ?", (professor_id,))
            central_prof = cursor.fetchone()
            
            if central_prof:
                nodes.append({
                    'id': professor_id,
                    'name': central_prof[0],
                    'university_id': central_prof[1],
                    'type': 'central',
                    'size': 20
                })
            
            # Add co-authors
            for coauthor in coauthors[:20]:  # Limit to top 20
                nodes.append({
                    'id': coauthor[0],
                    'name': coauthor[1],
                    'university_id': coauthor[2],
                    'type': 'coauthor',
                    'size': min(15, 5 + coauthor[3])
                })
                
                edges.append({
                    'source': professor_id,
                    'target': coauthor[0],
                    'weight': coauthor[3],
                    'type': 'collaboration'
                })
            
            # Add citation relationships
            for cited in cited_colleagues[:10]:  # Limit to top 10
                # Check if already added as coauthor
                if not any(node['id'] == cited[0] for node in nodes):
                    nodes.append({
                        'id': cited[0],
                        'name': cited[1],
                        'university_id': 0,  # Could be enhanced
                        'type': 'cited',
                        'size': min(12, 3 + cited[2])
                    })
                
                edges.append({
                    'source': professor_id,
                    'target': cited[0],
                    'weight': cited[2],
                    'type': 'citation'
                })
            
            return {
                'nodes': nodes,
                'edges': edges,
                'total_collaborators': len(coauthors),
                'total_cited_colleagues': len(cited_colleagues)
            }
            
        except Exception as e:
            logger.error(f"Error getting collaboration network: {str(e)}")
            return {'nodes': [], 'edges': [], 'total_collaborators': 0, 'total_cited_colleagues': 0}

class CitationVisualizer:
    """Generate visualization data for citation networks and metrics"""
    
    @staticmethod
    def prepare_network_data(network_data: Dict) -> str:
        """
        Prepare network data for JavaScript visualization
        
        Args:
            network_data (Dict): Network data with nodes and edges
            
        Returns:
            str: JSON string for JavaScript consumption
        """
        
        # Add colors and sizes based on node types
        for node in network_data.get('nodes', []):
            node_type = node.get('type', 'default')
            
            if node_type == 'central':
                node['color'] = '#e74c3c'
                node['size'] = 25
            elif node_type == 'coauthor':
                node['color'] = '#3498db'
                node['size'] = node.get('size', 15)
            elif node_type == 'cited':
                node['color'] = '#2ecc71'
                node['size'] = node.get('size', 12)
            else:
                node['color'] = '#95a5a6'
                node['size'] = 10
        
        # Add colors for edges
        for edge in network_data.get('edges', []):
            edge_type = edge.get('type', 'default')
            
            if edge_type == 'collaboration':
                edge['color'] = '#3498db'
                edge['width'] = min(5, edge.get('weight', 1))
            elif edge_type == 'citation':
                edge['color'] = '#2ecc71'
                edge['width'] = min(3, edge.get('weight', 1))
            else:
                edge['color'] = '#95a5a6'
                edge['width'] = 1
        
        return json.dumps(network_data)
    
    @staticmethod
    def prepare_metrics_chart_data(metrics: Dict) -> str:
        """
        Prepare citation metrics for chart visualization
        
        Args:
            metrics (Dict): Citation metrics data
            
        Returns:
            str: JSON string for chart visualization
        """
        
        # Prepare data for various charts
        chart_data = {
            'publications_by_year': {
                'labels': list(metrics.get('publications_by_year', {}).keys()),
                'data': list(metrics.get('publications_by_year', {}).values()),
                'type': 'bar',
                'title': 'Publications by Year'
            },
            'citations_by_year': {
                'labels': list(metrics.get('citations_by_year', {}).keys()),
                'data': list(metrics.get('citations_by_year', {}).values()),
                'type': 'line',
                'title': 'Citations by Year'
            },
            'key_metrics': {
                'h_index': metrics.get('h_index', 0),
                'total_citations': metrics.get('total_citations', 0),
                'total_publications': metrics.get('total_publications', 0),
                'i10_index': metrics.get('i10_index', 0),
                'average_citations': metrics.get('average_citations', 0),
                'citation_velocity': metrics.get('citation_velocity', 0)
            }
        }
        
        return json.dumps(chart_data)

def demo_citation_analysis():
    """Demonstrate citation analysis functionality"""
    
    print("📊 Citation Analysis Demo")
    print("=" * 40)
    
    # This would typically use a real database
    print("Citation analysis module ready for integration!")
    print("Features available:")
    print("  • H-index calculation")
    print("  • Citation metrics analysis")
    print("  • Collaboration network mapping")
    print("  • Top cited papers identification")
    print("  • Network visualization data preparation")

if __name__ == "__main__":
    demo_citation_analysis() 
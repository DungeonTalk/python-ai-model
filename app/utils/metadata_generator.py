"""
TRPG 문서 메타데이터 자동 생성 유틸리티
파일명, 경로, 내용을 기반으로 스마트하게 메타데이터를 생성합니다.
"""

import os
import re
from typing import Dict, List, Optional
from pathlib import Path

class MetadataGenerator:
    """TRPG 문서의 메타데이터를 자동으로 생성하는 클래스"""
    
    # 문서 타입 패턴 정의
    DOC_TYPE_PATTERNS = {
        "npc": ["npc", "캐릭터", "인물", "등장인물", "character"],
        "location": ["location", "장소", "지역", "마을", "던전", "도시", "숲", "산", "바다", "place"],
        "item": ["아이템", "무기", "방어구", "도구", "장비", "소모품", "item", "weapon", "armor", "tool"],
        "quest": ["퀘스트", "시나리오", "모험", "미션", "임무", "quest", "scenario", "mission"],
        "rule": ["규칙", "룰", "시스템", "매뉴얼", "가이드", "rule", "system", "manual"],
        "lore": ["세계관", "배경", "역사", "전설", "신화", "lore", "background", "history"],
        "event": ["이벤트", "사건", "상황", "encounter", "event"],
        "faction": ["집단", "조직", "길드", "세력", "faction", "guild", "organization"],
    }
    
    # 세계관 키워드 패턴
    WORLD_TYPE_PATTERNS = {
        "FANTASY": ["판타지", "fantasy", "마법", "엘프", "드워프", "오크", "마법사", "기사", "드래곤", "던전"],
        "SF": ["sf", "사이버", "우주", "로봇", "ai", "인공지능", "레이저", "우주선", "외계인", "미래"],
        "MODERN": ["현대", "도시", "경찰", "범죄", "스마트폰", "자동차", "회사", "아파트"],
        "HORROR": ["공포", "호러", "좀비", "유령", "악마", "저주", "괴물"],
        "WESTERN": ["서부", "카우보이", "보안관", "술집", "말", "총잡이"],
        "CYBERPUNK": ["사이버펑크", "해킹", "네온", "메가코프", "사이보그", "가상현실"],
        "STEAMPUNK": ["스팀펑크", "증기", "기계", "톱니바퀴", "발명가", "비행선"],
        "POST_APOCALYPTIC": ["포스트", "아포칼립스", "폐허", "생존", "방사능", "바이러스", "좀비"]
    }
    
    @staticmethod
    def extract_world_type_from_path(file_path: str) -> Optional[str]:
        """파일 경로에서 세계관 추출"""
        path_upper = file_path.upper()
        
        # 폴더명에서 직접 세계관 추출
        for world_type in MetadataGenerator.WORLD_TYPE_PATTERNS.keys():
            if world_type in path_upper:
                return world_type
        
        return None
    
    @staticmethod
    def detect_doc_type(filename: str, content: str = "") -> Dict[str, str]:
        """파일명과 내용으로 문서 타입 자동 감지"""
        filename_lower = filename.lower()
        content_lower = content.lower()[:500]  # 처음 500자만 분석
        
        # 파일명으로 1차 판단
        for doc_type, keywords in MetadataGenerator.DOC_TYPE_PATTERNS.items():
            if any(keyword in filename_lower for keyword in keywords):
                return {
                    "doc_type": doc_type,
                    "category": MetadataGenerator._get_category_by_type(doc_type),
                    "confidence": "high"
                }
        
        # 내용으로 2차 판단 (파일명에서 감지 못한 경우)
        if content:
            for doc_type, keywords in MetadataGenerator.DOC_TYPE_PATTERNS.items():
                keyword_count = sum(1 for keyword in keywords if keyword in content_lower)
                if keyword_count >= 2:  # 2개 이상의 키워드 매칭
                    return {
                        "doc_type": doc_type,
                        "category": MetadataGenerator._get_category_by_type(doc_type),
                        "confidence": "medium"
                    }
        
        return {
            "doc_type": "general", 
            "category": "misc",
            "confidence": "low"
        }
    
    @staticmethod
    def detect_world_type_from_content(content: str) -> Optional[str]:
        """문서 내용에서 세계관 추출"""
        content_lower = content.lower()
        
        # 각 세계관별 키워드 점수 계산
        world_scores = {}
        for world_type, keywords in MetadataGenerator.WORLD_TYPE_PATTERNS.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                world_scores[world_type] = score
        
        if world_scores:
            # 가장 높은 점수의 세계관 반환
            return max(world_scores, key=world_scores.get)
        
        return None
    
    @staticmethod
    def extract_auto_tags(filename: str, content: str) -> List[str]:
        """파일명과 내용에서 자동 태그 추출"""
        tags = []
        
        # 파일명에서 태그 추출
        filename_parts = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', filename).split()
        for part in filename_parts:
            if len(part) >= 2 and part not in ["txt", "md", "file", "doc"]:
                tags.append(part)
        
        # 내용에서 중요 키워드 추출 (간단한 휴리스틱)
        if content:
            # 인물명 패턴 (한글 이름)
            names = re.findall(r'[가-힣]{2,4}(?=\s|은|는|이|가|을|를)', content[:200])
            tags.extend(names[:3])  # 최대 3개 이름
            
            # 특수 키워드들
            special_keywords = [
                "마법사", "전사", "도둑", "궁수", "성직자",  # 직업
                "친절한", "사악한", "신비로운", "용감한",     # 성격
                "상점", "여관", "길드", "성", "마을",         # 장소 타입
                "검", "활", "지팡이", "갑옷", "방패"         # 아이템 타입
            ]
            
            for keyword in special_keywords:
                if keyword in content and keyword not in tags:
                    tags.append(keyword)
                    if len(tags) >= 10:  # 최대 10개 태그
                        break
        
        return tags[:8]  # 최대 8개 반환
    
    @staticmethod
    def generate_smart_metadata(file_path: str, content: str = "") -> Dict:
        """스마트 메타데이터 생성 (메인 함수)"""
        filename = Path(file_path).name
        
        # 1단계: 경로에서 세계관 추출
        world_type = MetadataGenerator.extract_world_type_from_path(file_path)
        
        # 2단계: 내용에서 세계관 보완
        if not world_type and content:
            world_type = MetadataGenerator.detect_world_type_from_content(content)
        
        # 3단계: 기본값 설정
        if not world_type:
            world_type = "FANTASY"  # 기본 세계관
        
        # 4단계: 문서 타입 감지
        doc_info = MetadataGenerator.detect_doc_type(filename, content)
        
        # 5단계: 자동 태그 생성
        auto_tags = MetadataGenerator.extract_auto_tags(filename, content)
        
        return {
            "world_type": world_type,
            "doc_type": doc_info["doc_type"],
            "category": doc_info["category"],
            "filename": filename,
            "file_path": file_path,
            "auto_tags": auto_tags,
            "user_tags": [],  # 사용자 추가 태그
            "confidence": doc_info["confidence"],
            "auto_generated": True
        }
    
    @staticmethod
    def _get_category_by_type(doc_type: str) -> str:
        """문서 타입에 따른 카테고리 반환"""
        category_map = {
            "npc": "character",
            "location": "world",
            "item": "equipment", 
            "quest": "scenario",
            "rule": "system",
            "lore": "world",
            "event": "scenario",
            "faction": "world",
            "general": "misc"
        }
        return category_map.get(doc_type, "misc")

# 테스트 함수
if __name__ == "__main__":
    # 테스트 케이스
    test_cases = [
        {
            "path": "documents/FANTASY/npcs/NPC_엘리사_여관주인.txt",
            "content": "엘리사는 마을의 여관을 운영하는 친절한 중년 여성이다. 모험가들에게 유용한 정보를 제공한다."
        },
        {
            "path": "documents/SF/locations/우주정거장_알파.txt", 
            "content": "알파 우주정거장은 화성 궤도상의 대형 우주시설이다. AI와 로봇들이 관리한다."
        }
    ]
    
    for case in test_cases:
        metadata = MetadataGenerator.generate_smart_metadata(case["path"], case["content"])
        print(f"\n파일: {case['path']}")
        print(f"메타데이터: {metadata}")
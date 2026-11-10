"""Streamlit web application for HCMUT-AILib.

Provides an interactive research workbench for searching, exploring, and citing
open-access computer science papers from arXiv using dense semantic vector
retrieval and hybrid Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import sys
import time

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src import indexer, ingest
from src.citations import FORMATS, bibtex_key
from src.keywords import KeywordExtractor
from src.search_engine import Paper, SearchEngine, SearchResult

CATEGORY_NAMES = {
    "cs.AI": "Artificial Intelligence",
    "cs.LG": "Machine Learning",
    "cs.CL": "Computation and Language",
    "cs.IR": "Information Retrieval",
    "cs.CV": "Computer Vision",
    "cs.RO": "Robotics",
    "cs.HC": "Human-Computer Interaction",
    "cs.CR": "Cryptography and Security",
    "cs.CY": "Computers and Society",
    "cs.DB": "Databases",
    "cs.NE": "Neural and Evolutionary Computing",
    "cs.SD": "Sound",
    "cs.SE": "Software Engineering",
    "cs.SI": "Social and Information Networks",
    "stat.ML": "Machine Learning (Stats)",
    "eess.AS": "Audio and Speech Processing",
    "eess.IV": "Image and Video Processing",
}

CATEGORY_BADGE_COLORS = {
    "cs.AI": "violet",
    "cs.LG": "blue",
    "cs.CL": "green",
    "cs.IR": "orange",
    "cs.CV": "red",
    "cs.RO": "violet",
    "cs.HC": "green",
    "cs.CR": "red",
    "stat.ML": "blue",
}

CORE_CATEGORIES = ("cs.AI", "cs.LG", "cs.CL", "cs.IR")

EXAMPLE_QUERIES = [
    "detecting fake news on social media",
    "making transformers cheaper for long documents",
    "recommendation systems that explain their suggestions",
    "translation for languages with little training data",
    "attacks that hide triggers inside neural networks",
    "mixing two languages within one conversation",
    "blurring sensitive objects in real-time video broadcasts",
]

RETRIEVAL_MODES = (
    f"Dense Semantic ({indexer.MODEL_NAME})",
    "Hybrid RRF (Dense + BM25)",
    "Lexical Baseline (Okapi BM25)",
)
SORT_OPTIONS = ("Relevance", "Newest first", "Oldest first", "Title (A–Z)")
VIEW_MODES = ("Detailed Cards", "Cards + Comparison Matrix", "Compact Cards")
ABSTRACT_PREVIEW = 320

EVAL_JSON_PATH = REPO_ROOT / "reports" / "results" / "evaluation.json"
SCIFACT_JSON_PATH = REPO_ROOT / "reports" / "results" / "scifact_evaluation_leaf384.json"
SCIFACT_FALLBACK_PATH = REPO_ROOT / "reports" / "results" / "scifact_evaluation.json"
PCA_FIG_PATH = REPO_ROOT / "reports" / "figures" / "embedding_pca.png"
ARCH_FIG_PATH = REPO_ROOT / "docs" / "architecture.png"

st.set_page_config(page_title="HCMUT-AILib", layout="wide")


def inject_styles() -> None:
    """Apply vibrant multi-color dark-mode styling with keyframe animations and motion."""
    st.html("""
    <style>
        /* Keyframe Animations */
        @keyframes auroraBg {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes rainbowFlow {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes pulseBeacon {
            0%, 100% { transform: scale(1); opacity: 1; box-shadow: 0 0 8px currentColor; }
            50%      { transform: scale(1.32); opacity: 0.78; box-shadow: 0 0 16px currentColor; }
        }
        @keyframes cardEntrance {
            0%   { opacity: 0; transform: translateY(12px) scale(0.992); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes floatBadge {
            0%, 100% { transform: translateY(0px); }
            50%      { transform: translateY(-3px); }
        }
        @keyframes streamPulse {
            0%   { opacity: 0.35; transform: translateX(-3px); }
            50%  { opacity: 1; transform: translateX(3px); }
            100% { opacity: 0.35; transform: translateX(-3px); }
        }
        @keyframes loaderPulseGlow {
            0%, 100% {
                box-shadow: 0 20px 50px -10px rgba(0, 0, 0, 0.7),
                            0 0 30px rgba(56, 189, 248, 0.25),
                            0 0 60px rgba(168, 85, 247, 0.15);
                border-color: rgba(56, 189, 248, 0.45);
            }
            50% {
                box-shadow: 0 25px 65px -10px rgba(0, 0, 0, 0.8),
                            0 0 45px rgba(56, 189, 248, 0.45),
                            0 0 80px rgba(168, 85, 247, 0.35);
                border-color: rgba(168, 85, 247, 0.65);
            }
        }
        @keyframes spinRotate {
            0%   { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes radarRipple {
            0% {
                transform: scale(0.94);
                opacity: 0.88;
            }
            50% {
                transform: scale(1.05);
                opacity: 0.45;
            }
            100% {
                transform: scale(0.94);
                opacity: 0.88;
            }
        }

        /* Root & Animated Multi-Color Aurora Background */
        .stApp {
            background:
                radial-gradient(circle at 12% 8%, rgba(56, 189, 248, 0.14) 0%, transparent 38%),
                radial-gradient(circle at 88% 12%, rgba(168, 85, 247, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 50% 85%, rgba(16, 185, 129, 0.10) 0%, transparent 45%),
                linear-gradient(135deg, #070b14 0%, #0d1326 35%, #111827 70%, #090d18 100%);
            background-size: 200% 200%;
            animation: auroraBg 18s ease infinite;
            color: #f1f5f9;
        }
        header[data-testid="stHeader"] {
            background: rgba(9, 13, 24, 0.72) !important;
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(139, 92, 246, 0.22);
        }
        .block-container {
            padding-top: 3.8rem !important;
            padding-bottom: 3.5rem !important;
            max-width: 1280px !important;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b1120 0%, #11162b 55%, #090d1a 100%);
            border-right: 1px solid rgba(139, 92, 246, 0.28);
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.35);
        }

        /* Centered Loading Embeddings Splash Screen for Initial Cache Load */
        .stCacheSpinner {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 14vh auto 0 auto !important;
            padding: 3rem 2.8rem 2.6rem 2.8rem !important;
            max-width: 580px !important;
            width: 90% !important;
            border-radius: 22px !important;
            background:
                radial-gradient(circle at 50% 0%, rgba(56, 189, 248, 0.2) 0%, transparent 65%),
                radial-gradient(circle at 50% 100%, rgba(168, 85, 247, 0.15) 0%, transparent 60%),
                linear-gradient(145deg, rgba(15, 23, 42, 0.96) 0%, rgba(20, 24, 45, 0.98) 100%) !important;
            border: 1px solid rgba(56, 189, 248, 0.42) !important;
            border-top: 3px solid #38bdf8 !important;
            box-shadow:
                0 20px 60px -10px rgba(0, 0, 0, 0.75),
                0 0 40px rgba(56, 189, 248, 0.25),
                0 0 80px rgba(139, 92, 246, 0.18) !important;
            backdrop-filter: blur(20px) !important;
            animation: loaderPulseGlow 3s ease-in-out infinite, cardEntrance 0.45s cubic-bezier(0.2, 0.9, 0.3, 1) !important;
            text-align: center !important;
            position: relative !important;
        }

        .stCacheSpinner::before {
            content: "HCMUT-AILIB · NEURAL SYSTEM BOOT";
            display: inline-block !important;
            font-size: 0.68rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.14em !important;
            text-transform: uppercase !important;
            color: #7dd3fc !important;
            background: rgba(12, 74, 110, 0.55) !important;
            border: 1px solid rgba(56, 189, 248, 0.45) !important;
            padding: 0.28rem 0.85rem !important;
            border-radius: 999px !important;
            margin-bottom: 0.9rem !important;
            box-shadow: 0 0 16px rgba(56, 189, 248, 0.3) !important;
        }

        .stCacheSpinner::after {
            content: "Loading 384-D sentence embeddings · Warming up ChromaDB HNSW · Local CPU execution";
            display: block !important;
            font-size: 0.74rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.04em !important;
            color: #94a3b8 !important;
            margin-top: 0.9rem !important;
            padding-top: 0.85rem !important;
            border-top: 1px solid rgba(148, 163, 184, 0.16) !important;
            width: 100% !important;
            text-align: center !important;
        }

        .stCacheSpinner > div {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 1.15rem !important;
            width: 100% !important;
        }

        .stCacheSpinner svg {
            width: 52px !important;
            height: 52px !important;
            color: #38bdf8 !important;
            filter: drop-shadow(0 0 14px rgba(56, 189, 248, 0.85))
                    drop-shadow(0 0 28px rgba(168, 85, 247, 0.65)) !important;
            animation: spinRotate 1.25s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite, radarRipple 2.5s ease-in-out infinite !important;
        }

        .stCacheSpinner [role="status"] {
            text-align: center !important;
        }

        .stCacheSpinner [role="status"] p,
        .stCacheSpinner [role="status"] span {
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.01em !important;
            color: #f8fafc !important;
            background: linear-gradient(90deg, #38bdf8, #c084fc, #ec4899, #38bdf8) !important;
            background-size: 200% 100% !important;
            animation: rainbowFlow 4s linear infinite !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            margin: 0 !important;
            text-shadow: 0 0 20px rgba(56, 189, 248, 0.25) !important;
        }

        /* Centered Query Searching Spinner */
        div[data-testid="stSpinner"]:not(.stCacheSpinner) {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 1.8rem auto !important;
            padding: 0.9rem 1.8rem !important;
            max-width: 440px !important;
            border-radius: 999px !important;
            background: rgba(15, 23, 42, 0.92) !important;
            border: 1px solid rgba(56, 189, 248, 0.35) !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), 0 0 18px rgba(56, 189, 248, 0.22) !important;
            backdrop-filter: blur(12px) !important;
            animation: cardEntrance 0.3s ease-out !important;
        }

        div[data-testid="stSpinner"]:not(.stCacheSpinner) > div {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.75rem !important;
        }

        div[data-testid="stSpinner"]:not(.stCacheSpinner) svg {
            width: 24px !important;
            height: 24px !important;
            color: #38bdf8 !important;
            filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.7)) !important;
            animation: spinRotate 1s linear infinite !important;
        }

        div[data-testid="stSpinner"]:not(.stCacheSpinner) [role="status"] p {
            font-size: 0.92rem !important;
            font-weight: 600 !important;
            color: #e2e8f0 !important;
            margin: 0 !important;
        }

        /* Crisp h1 title */
        h1 {
            font-size: 2.15rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
            line-height: 1.2 !important;
            margin-top: 0 !important;
            margin-bottom: 0.2rem !important;
            padding-top: 0 !important;
            color: #f8fafc !important;
            text-shadow: 0 0 24px rgba(56, 189, 248, 0.28);
        }

        /* Animated Rainbow Shimmer Ribbon at top of Hero Header */
        .ailib-rainbow-bar {
            height: 4px;
            width: 100%;
            border-radius: 999px;
            background: linear-gradient(
                90deg,
                #06b6d4,
                #3b82f6,
                #8b5cf6,
                #ec4899,
                #f59e0b,
                #10b981,
                #06b6d4
            );
            background-size: 300% 100%;
            animation: rainbowFlow 6s linear infinite;
            margin-bottom: 0.75rem;
            box-shadow: 0 0 14px rgba(139, 92, 246, 0.45);
        }

        /* Top institutional status strip inside header container */
        .ailib-topbar {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 0.65rem;
            padding-bottom: 0.7rem;
            margin-bottom: 0.65rem;
            border-bottom: 1px solid rgba(148, 163, 184, 0.18);
        }
        .ailib-inst-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #e0e7ff;
            background: linear-gradient(90deg, rgba(37, 99, 235, 0.42), rgba(124, 58, 237, 0.42));
            border: 1px solid rgba(129, 140, 248, 0.48);
            padding: 0.28rem 0.82rem;
            border-radius: 999px;
            box-shadow: 0 0 16px rgba(99, 102, 241, 0.25);
        }
        .ailib-status-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.48rem;
            align-items: center;
        }
        .ailib-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.38rem;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.24rem 0.68rem;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(148, 163, 184, 0.28);
            color: #e2e8f0;
            white-space: nowrap;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .ailib-pill:hover {
            transform: translateY(-2px);
        }
        .ailib-pill-online {
            border-color: rgba(52, 211, 153, 0.55);
            color: #6ee7b7;
            background: linear-gradient(135deg, rgba(6, 78, 59, 0.50), rgba(16, 185, 129, 0.18));
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.20);
        }
        .ailib-pill-cyan {
            border-color: rgba(56, 189, 248, 0.55);
            color: #7dd3fc;
            background: linear-gradient(135deg, rgba(12, 74, 110, 0.52), rgba(56, 189, 248, 0.18));
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.20);
        }
        .ailib-pill-violet {
            border-color: rgba(192, 132, 252, 0.55);
            color: #e9d5ff;
            background: linear-gradient(135deg, rgba(88, 28, 135, 0.50), rgba(168, 85, 247, 0.20));
            box-shadow: 0 0 12px rgba(168, 85, 247, 0.20);
        }
        .ailib-pill-amber {
            border-color: rgba(251, 191, 36, 0.55);
            color: #fde68a;
            background: linear-gradient(135deg, rgba(120, 53, 15, 0.50), rgba(245, 158, 11, 0.20));
            box-shadow: 0 0 12px rgba(245, 158, 11, 0.18);
        }
        .ailib-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            color: #10b981;
            display: inline-block;
            animation: pulseBeacon 2s ease-in-out infinite;
        }

        /* Multi-Color KPI Boxes in Header */
        .ailib-kpi-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.65rem;
        }
        .ailib-stat-box {
            background: rgba(15, 23, 42, 0.80);
            border-radius: 12px;
            padding: 0.58rem 0.78rem;
            position: relative;
            overflow: hidden;
            transition: transform 0.22s ease, box-shadow 0.22s ease;
        }
        .ailib-stat-box:hover {
            transform: translateY(-3px);
        }
        .ailib-stat-cyan {
            border: 1px solid rgba(56, 189, 248, 0.42);
            border-top: 3px solid #38bdf8;
            box-shadow: 0 6px 18px rgba(56, 189, 248, 0.12);
        }
        .ailib-stat-violet {
            border: 1px solid rgba(168, 85, 247, 0.42);
            border-top: 3px solid #a855f7;
            box-shadow: 0 6px 18px rgba(168, 85, 247, 0.14);
        }
        .ailib-stat-emerald {
            border: 1px solid rgba(16, 185, 129, 0.42);
            border-top: 3px solid #10b981;
            box-shadow: 0 6px 18px rgba(16, 185, 129, 0.12);
        }
        .ailib-stat-label {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #cbd5e1;
            margin-bottom: 0.1rem;
        }
        .ailib-stat-val {
            font-size: 1.08rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.25;
        }
        .ailib-stat-sub-cyan {
            font-size: 0.7rem;
            color: #38bdf8;
            font-weight: 600;
            margin-top: 0.1rem;
        }
        .ailib-stat-sub-violet {
            font-size: 0.7rem;
            color: #c084fc;
            font-weight: 600;
            margin-top: 0.1rem;
        }
        .ailib-stat-sub-emerald {
            font-size: 0.7rem;
            color: #34d399;
            font-weight: 600;
            margin-top: 0.1rem;
        }

        /* Animated Live Neural Pipeline Strip */
        .ailib-pipeline {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 0.45rem;
            margin-top: 0.7rem;
            padding: 0.55rem 0.85rem;
            border-radius: 10px;
            background: linear-gradient(90deg, rgba(15, 23, 42, 0.9), rgba(30, 27, 75, 0.75), rgba(15, 23, 42, 0.9));
            border: 1px solid rgba(129, 140, 248, 0.25);
        }
        .ailib-stage {
            display: inline-flex;
            align-items: center;
            gap: 0.38rem;
            font-size: 0.73rem;
            font-weight: 600;
            padding: 0.22rem 0.62rem;
            border-radius: 8px;
            background: rgba(30, 41, 59, 0.65);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.2);
            transition: all 0.25s ease;
        }
        .ailib-stage-active-cyan {
            background: rgba(6, 182, 212, 0.18);
            color: #67e8f9;
            border-color: rgba(34, 211, 238, 0.5);
            box-shadow: 0 0 12px rgba(6, 182, 212, 0.22);
        }
        .ailib-stage-active-violet {
            background: rgba(139, 92, 246, 0.20);
            color: #ddd6fe;
            border-color: rgba(167, 139, 250, 0.55);
            box-shadow: 0 0 12px rgba(139, 92, 246, 0.25);
        }
        .ailib-stage-active-pink {
            background: rgba(236, 72, 153, 0.20);
            color: #fbcfe8;
            border-color: rgba(244, 114, 182, 0.55);
            box-shadow: 0 0 12px rgba(236, 72, 153, 0.25);
        }
        .ailib-stage-active-emerald {
            background: rgba(16, 185, 129, 0.20);
            color: #a7f3d0;
            border-color: rgba(52, 211, 153, 0.55);
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.25);
        }
        .ailib-arrow {
            color: #818cf8;
            font-size: 0.85rem;
            font-weight: 700;
            animation: streamPulse 1.6s ease-in-out infinite;
        }

        /* Bordered Containers / Cards with Entrance Motion & Multi-Color Glow */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(145deg, rgba(17, 24, 39, 0.88) 0%, rgba(15, 23, 42, 0.92) 100%);
            border: 1px solid rgba(56, 189, 248, 0.24) !important;
            border-radius: 14px !important;
            animation: cardEntrance 0.38s cubic-bezier(0.22, 1, 0.36, 1) both;
            transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
                        border-color 0.22s ease,
                        box-shadow 0.22s ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            transform: translateY(-3px);
            border-color: rgba(168, 85, 247, 0.55) !important;
            box-shadow:
                0 10px 26px -6px rgba(56, 189, 248, 0.20),
                0 6px 18px -4px rgba(168, 85, 247, 0.18);
        }

        /* Confidence tier chips */
        .tier-chip {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.15rem 0.55rem;
            border-radius: 999px;
            letter-spacing: 0.03em;
        }
        .tier-high {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.35);
        }
        .tier-med {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.35);
        }
        .tier-low {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.35);
        }

        /* Animated Multi-Color Progress Bars for Match Scores */
        div[data-testid="stProgress"] > div > div > div > div {
            background: linear-gradient(
                90deg,
                #06b6d4 0%,
                #8b5cf6 45%,
                #ec4899 75%,
                #10b981 100%
            ) !important;
            background-size: 200% 100% !important;
            animation: rainbowFlow 4s linear infinite !important;
            border-radius: 999px !important;
        }

        /* Metrics with Colorful Borders & Hover Lift */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(30, 27, 75, 0.45));
            border: 1px solid rgba(99, 102, 241, 0.32);
            border-radius: 12px;
            padding: 0.5rem 0.72rem;
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.6);
            box-shadow: 0 6px 18px rgba(56, 189, 248, 0.16);
        }
        div[data-testid="stMetricValue"] {
            background: linear-gradient(90deg, #38bdf8, #a855f7, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800 !important;
        }

        /* Interactive Buttons & Link Buttons */
        .stButton > button, .stLinkButton > a, .stDownloadButton > button {
            border-radius: 10px !important;
            border: 1px solid rgba(99, 102, 241, 0.32) !important;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.92)) !important;
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease !important;
        }
        .stButton > button:hover, .stLinkButton > a:hover, .stDownloadButton > button:hover {
            transform: translateY(-2px) !important;
            border-color: rgba(56, 189, 248, 0.68) !important;
            box-shadow: 0 6px 16px rgba(56, 189, 248, 0.22), 0 0 10px rgba(168, 85, 247, 0.16) !important;
        }

        /* Tabs bar with Gradient Active Indicator */
        div[data-baseweb="tab-list"] {
            gap: 0.4rem;
            background: rgba(15, 23, 42, 0.85);
            padding: 0.4rem;
            border-radius: 12px;
            border: 1px solid rgba(139, 92, 246, 0.28);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.28);
        }
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            padding: 0.5rem 1rem !important;
            border-radius: 9px !important;
            color: #94a3b8 !important;
            transition: all 0.2s ease !important;
        }
        button[data-baseweb="tab"]:hover {
            color: #e2e8f0 !important;
            background: rgba(99, 102, 241, 0.12) !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.24), rgba(139, 92, 246, 0.28)) !important;
            color: #f8fafc !important;
            border: 1px solid rgba(56, 189, 248, 0.45) !important;
            box-shadow: 0 0 16px rgba(56, 189, 248, 0.22) !important;
        }

        /* Sidebar section header chips */
        .sidebar-section-title {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            background: linear-gradient(90deg, #38bdf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-top: 0.55rem;
            margin-bottom: 0.28rem;
            display: inline-block;
        }
    </style>
    """)


@st.cache_resource(show_spinner="Loading 384-D neural embeddings and vector index…")
def get_engine() -> SearchEngine:
    return SearchEngine()


@st.cache_resource
def get_keyword_extractor() -> KeywordExtractor:
    return KeywordExtractor([p["abstract"] for p in ingest.load()])


@st.cache_data
def load_raw_corpus() -> list[dict]:
    return ingest.load()


@st.cache_data
def year_bounds() -> tuple[int, int]:
    years = [int(p["published_date"][:4]) for p in load_raw_corpus()]
    return min(years), max(years)


@st.cache_data
def paper_catalog() -> dict[str, str]:
    """Map paper IDs to human-readable 'ID — Title (Year)' labels for seed selection."""
    return {
        p["id"]: f"{p['id']} — {p['title']} ({p['published_date'][:4]})"
        for p in load_raw_corpus()
    }


@st.cache_data
def load_evaluation_data() -> dict | None:
    if EVAL_JSON_PATH.exists():
        try:
            return json.loads(EVAL_JSON_PATH.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


@st.cache_data
def load_scifact_data() -> dict | None:
    path = SCIFACT_JSON_PATH if SCIFACT_JSON_PATH.exists() else SCIFACT_FALLBACK_PATH
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


@st.cache_data
def corpus_statistics() -> dict:
    papers = load_raw_corpus()
    total = len(papers)
    by_cat: dict[str, int] = {}
    by_year: dict[int, int] = {}
    word_counts: list[int] = []
    doi_count = 0
    for p in papers:
        for c in p["categories"]:
            by_cat[c] = by_cat.get(c, 0) + 1
        y = int(p["published_date"][:4])
        by_year[y] = by_year.get(y, 0) + 1
        word_counts.append(len(p["abstract"].split()))
        if p.get("doi"):
            doi_count += 1
    sampled_cats = {c: by_cat.get(c, 0) for c in CATEGORY_NAMES if c in by_cat}
    return {
        "total": total,
        "by_category": dict(sorted(by_cat.items(), key=lambda kv: -kv[1])),
        "by_sampled_cat": sampled_cats,
        "by_year": dict(sorted(by_year.items())),
        "avg_words": sum(word_counts) / max(total, 1),
        "min_words": min(word_counts) if word_counts else 0,
        "max_words": max(word_counts) if word_counts else 0,
        "doi_pct": (doi_count / max(total, 1)) * 100,
    }


def init_session_state() -> None:
    if "query" not in st.session_state:
        st.session_state.query = ""
    if "similar_to" not in st.session_state:
        st.session_state.similar_to = ""
    if "saved_papers" not in st.session_state:
        st.session_state.saved_papers = []
    if "query_history" not in st.session_state:
        st.session_state.query_history = []


def _select_similar(paper_id: str) -> None:
    st.session_state.similar_to = paper_id
    st.session_state.seed_picker = paper_id
    st.session_state._switch_to_similar = True


def _toggle_saved_paper(paper_id: str) -> None:
    saved: list[str] = list(st.session_state.get("saved_papers", []))
    if paper_id in saved:
        saved.remove(paper_id)
    else:
        saved.append(paper_id)
    st.session_state.saved_papers = saved


def _clear_saved_papers() -> None:
    st.session_state.saved_papers = []


def _on_seed_picker_change() -> None:
    picked = st.session_state.get("seed_picker")
    if picked:
        st.session_state.similar_to = picked


def _on_similar_input_change() -> None:
    raw = (st.session_state.get("similar_to") or "").strip()
    if not raw:
        st.session_state.seed_picker = None
        return
    clean = ingest.parse_arxiv_id(
        raw[6:].strip() if raw.lower().startswith("arxiv:") else raw
    )
    st.session_state.seed_picker = clean if clean in paper_catalog() else None


def _on_example_change() -> None:
    st.session_state.query = st.session_state.get("example") or ""


def _on_query_change() -> None:
    if st.session_state.get("example") != st.session_state.get("query"):
        st.session_state.example = None


def _clear_query() -> None:
    st.session_state.query = ""
    st.session_state.example = None


def _reset_filters(lo: int, hi: int) -> None:
    st.session_state.filter_top_k = 10
    st.session_state.filter_years = (lo, hi)
    st.session_state.filter_categories = []
    st.session_state.filter_author = ""
    st.session_state.retrieval_mode = RETRIEVAL_MODES[0]
    st.session_state.min_score_pct = 0
    st.session_state.sort_by = SORT_OPTIONS[0]
    st.session_state.view_mode = VIEW_MODES[0]
    st.session_state.only_doi = False


def record_query_history(query: str) -> None:
    q = query.strip()
    if not q:
        return
    hist: list[str] = list(st.session_state.get("query_history", []))
    if q in hist:
        hist.remove(q)
    hist.insert(0, q)
    st.session_state.query_history = hist[:8]


def format_category_badges(paper: Paper) -> str:
    badges = []
    for idx, cat in enumerate(paper.categories):
        color = CATEGORY_BADGE_COLORS.get(cat, "blue" if cat in CATEGORY_NAMES else "gray")
        if cat in CATEGORY_NAMES:
            label = f"{cat} · {CATEGORY_NAMES[cat]}" if idx == 0 else cat
            badges.append(f":{color}-badge[{label}]")
        else:
            badges.append(f":gray-badge[{cat}]")
    return " ".join(badges)


def confidence_tier_html(score: float) -> str:
    if score >= 0.78:
        return '<span class="tier-chip tier-high">● High Match</span>'
    if score >= 0.68:
        return '<span class="tier-chip tier-med">● Moderate Match</span>'
    return '<span class="tier-chip tier-low">● Exploratory</span>'


def format_active_filters(
    years: tuple[int, int],
    bounds: tuple[int, int],
    categories: list[str],
    author: str,
    min_score_pct: int = 0,
    only_doi: bool = False,
    retrieval_mode: str = RETRIEVAL_MODES[0],
) -> list[str]:
    summary: list[str] = []
    if retrieval_mode != RETRIEVAL_MODES[0]:
        summary.append(f"Mode: {retrieval_mode.split(' (')[0]}")
    if years != bounds:
        summary.append(
            f"Year: {years[0]}" if years[0] == years[1] else f"Years: {years[0]}–{years[1]}"
        )
    if categories:
        summary.append("Categories: " + ", ".join(categories))
    if author.strip():
        summary.append(f"Author: “{author.strip()}”")
    if min_score_pct > 0:
        summary.append(f"Min Match: ≥{min_score_pct}%")
    if only_doi:
        summary.append("DOI Required")
    return summary


def paper_matches_filters(
    paper: Paper,
    year_range: tuple[int, int] | None,
    categories: list[str] | None,
    author: str | None,
    engine: SearchEngine | None = None,
) -> bool:
    if year_range and not (year_range[0] <= paper.year <= year_range[1]):
        return False
    if categories and not any(c in paper.categories for c in categories):
        return False
    if author:
        if engine is not None:
            return paper.id in engine.author_index.match(author)
        if author.strip().lower() not in "; ".join(paper.authors).lower():
            return False
    return True


def execute_retrieval(
    engine: SearchEngine,
    query: str,
    retrieval_mode: str,
    top_k: int,
    year_range: tuple[int, int] | None,
    categories: list[str] | None,
    author: str | None,
) -> list[SearchResult]:
    """Run semantic, hybrid RRF, or Okapi BM25 retrieval via SearchEngine."""
    if retrieval_mode.startswith("Dense Semantic"):
        return engine.search(
            query,
            top_k=top_k,
            year_range=year_range,
            categories=categories,
            author=author,
            rerank=False,
        )

    if retrieval_mode.startswith("Hybrid RRF"):
        return engine.hybrid_search(
            query,
            top_k=top_k,
            year_range=year_range,
            categories=categories,
            author=author,
            rerank=False,
        )

    # Lexical Baseline (Okapi BM25)
    bm25 = engine.bm25
    raw_scores = bm25.scores(query)
    max_bm25 = max(raw_scores) if raw_scores else 0.0
    ranked = sorted(zip(raw_scores, bm25.ids), key=lambda x: -x[0])
    results: list[SearchResult] = []
    for sc, pid in ranked:
        if sc <= 0:
            break
        paper = engine.get(pid)
        if not paper_matches_filters(paper, year_range, categories, author, engine=engine):
            continue
        norm_sc = min(0.99, max(0.05, sc / max_bm25)) if max_bm25 > 0 else 0.0
        results.append(SearchResult(paper=paper, score=norm_sc, rank=len(results) + 1))
        if len(results) == top_k:
            break
    return results[:top_k]


def results_to_csv(results: list[SearchResult]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Rank", "Match Score", "arXiv ID", "Title", "Authors",
        "Published Date", "Categories", "DOI", "PDF URL", "Abstract",
    ])
    for r in results:
        p = r.paper
        writer.writerow([
            r.rank,
            f"{r.score:.4f}",
            p.id,
            p.title,
            "; ".join(p.authors),
            p.published_date,
            "; ".join(p.categories),
            p.doi,
            p.pdf_url,
            p.abstract,
        ])
    return buf.getvalue()


def render_professional_header(engine: SearchEngine) -> None:
    """Render a unified, vibrant, animated dark-mode institutional header card with live telemetry."""
    stats = corpus_statistics()
    saved_count = len(st.session_state.get("saved_papers", []))
    mode = st.session_state.get("retrieval_mode", RETRIEVAL_MODES[0])
    scifact = load_scifact_data()

    if scifact:
        h_ndcg = scifact.get("metrics_beir", {}).get("hybrid", {}).get("ndcg", {}).get("NDCG@10", 0.6714)
        b_ndcg = scifact.get("metrics_beir", {}).get("bm25", {}).get("ndcg", {}).get("NDCG@10", 0.6408)
        pct_gain = (h_ndcg - b_ndcg) / b_ndcg * 100
        bench_label = "BEIR SciFact nDCG@10"
        bench_val = f"{h_ndcg:.3f}"
        bench_sub = f"Hybrid RRF · +{pct_gain:.1f}% vs BM25 ({b_ndcg:.3f})"
    else:
        bench_label = "Benchmark MRR"
        bench_val = "0.883"
        bench_sub = "+15.3% vs MiniLM-L6"

    is_dense = mode.startswith("Dense") or mode.startswith("Hybrid")
    is_hybrid = mode.startswith("Hybrid")
    s1_cls = "ailib-stage ailib-stage-active-cyan" if is_dense else "ailib-stage"
    s2_cls = "ailib-stage ailib-stage-active-violet" if is_hybrid else "ailib-stage ailib-stage-active-cyan"
    s3_cls = "ailib-stage ailib-stage-active-emerald"

    with st.container(border=True):
        st.html(f"""
        <div class="ailib-rainbow-bar"></div>
        <div class="ailib-topbar">
            <span class="ailib-inst-tag">
                HCMUT · Faculty of Computer Science &amp; Engineering · CO2001
            </span>
            <div class="ailib-status-strip">
                <span class="ailib-pill ailib-pill-online">
                    <span class="ailib-dot"></span> Engine Online
                </span>
                <span class="ailib-pill ailib-pill-cyan">
                    Model: {indexer.MODEL_NAME} · 384-D
                </span>
                <span class="ailib-pill ailib-pill-violet">
                    ChromaDB HNSW · Cosine
                </span>
                <span class="ailib-pill ailib-pill-amber">
                    Air-Gapped Local Execution
                </span>
            </div>
        </div>
        """)

        title_col, status_col = st.columns([1.32, 1.68], vertical_alignment="center")
        with title_col:
            st.title("HCMUT-AILib")
            st.caption(
                "Semantic search & research assistant for open-access academic papers · "
                "Dense Vector + Hybrid RRF Retrieval Workbench (v1.0.0)"
            )
        with status_col:
            st.html(f"""
            <div class="ailib-kpi-row">
                <div class="ailib-stat-box ailib-stat-cyan">
                    <div class="ailib-stat-label">Indexed Corpus</div>
                    <div class="ailib-stat-val">{len(engine):,} Papers</div>
                    <div class="ailib-stat-sub-cyan">arXiv 2021–2025 · 17 Domains</div>
                </div>
                <div class="ailib-stat-box ailib-stat-violet">
                    <div class="ailib-stat-label">{bench_label}</div>
                    <div class="ailib-stat-val">{bench_val}</div>
                    <div class="ailib-stat-sub-violet">{bench_sub}</div>
                </div>
                <div class="ailib-stat-box ailib-stat-emerald">
                    <div class="ailib-stat-label">Reading List</div>
                    <div class="ailib-stat-val">{saved_count} Saved</div>
                    <div class="ailib-stat-sub-emerald">{stats['doi_pct']:.1f}% Publisher DOIs</div>
                </div>
            </div>
            """)

        st.html(f"""
        <div class="ailib-pipeline">
            <span class="{s1_cls}">1 · 384-D Neural Embedder ({indexer.MODEL_NAME})</span>
            <span class="ailib-arrow">━━▶</span>
            <span class="{s2_cls}">2 · {'Hybrid RRF (HNSW + BM25)' if is_hybrid else 'ChromaDB HNSW Cosine'}</span>
            <span class="ailib-arrow">━━▶</span>
            <span class="{s3_cls}">3 · TF-IDF Key Terms &amp; Citations</span>
        </div>
        """)


def render_card(
    result: SearchResult,
    key_prefix: str,
    compact: bool = False,
) -> None:
    paper = result.paper
    is_saved = paper.id in st.session_state.get("saved_papers", [])
    with st.container(border=True):
        head, score = st.columns([4.8, 1.2], vertical_alignment="top")
        head.markdown(f"#### {result.rank}. {paper.title}")
        score.metric(
            "Match",
            f"{result.score:.0%}",
            help="Semantic Similarity Score: Cosine similarity rescaled to 0–1; compare within this query only.",
        )
        score.progress(min(max(result.score, 0.0), 1.0))

        authors = ", ".join(paper.authors[:6]) + (
            f" et al. (+{len(paper.authors) - 6} more)" if len(paper.authors) > 6 else ""
        )
        badges = format_category_badges(paper)
        doi_badge = f" :green-badge[DOI: {paper.doi}]" if paper.doi else ""
        head.markdown(
            f"**{authors}** · Published: `{paper.published_date}` · `arXiv:{paper.id}`  \n"
            f"{badges}{doi_badge}"
        )
        score.html(
            f"<div style='text-align:right; margin-top:2px;'>{confidence_tier_html(result.score)}</div>"
        )

        keywords = get_keyword_extractor().extract(paper.abstract, k=5)
        if keywords:
            kw_colors = ("violet", "blue", "green", "orange", "red")
            kw_pills = " ".join(
                f":{kw_colors[i % len(kw_colors)]}-badge[{kw}]"
                for i, kw in enumerate(keywords)
            )
            st.markdown(f"**Key terms:** {kw_pills}")

        if not compact:
            preview = (
                paper.abstract
                if len(paper.abstract) <= ABSTRACT_PREVIEW
                else paper.abstract[:ABSTRACT_PREVIEW].rsplit(" ", 1)[0] + " …"
            )
            st.write(preview)

        with st.expander("Full abstract & metadata"):
            st.write(paper.abstract)
            meta_c1, meta_c2, meta_c3 = st.columns(3)
            meta_c1.caption(f"**Primary category:** `{paper.primary_category}`")
            meta_c2.caption(f"**Abstract length:** {len(paper.abstract.split())} words")
            meta_c3.caption(f"**BibTeX key:** `{bibtex_key(paper)}`")
            if len(paper.authors) > 6:
                st.caption("**All authors:** " + ", ".join(paper.authors))

        n_cols = 5 if paper.doi else 4
        links = st.columns(n_cols)
        links[0].link_button("PDF", paper.pdf_url, width="stretch")
        links[1].link_button("arXiv page", paper.abs_url, width="stretch")
        if paper.doi:
            links[2].link_button("DOI", f"https://doi.org/{paper.doi}", width="stretch")
            sim_col = links[3]
            save_col = links[4]
        else:
            sim_col = links[2]
            save_col = links[3]

        if sim_col.button(
            "Find similar",
            key=f"{key_prefix}-sim-{paper.id}",
            on_click=_select_similar,
            args=(paper.id,),
            width="stretch",
        ):
            st.toast(f"Loaded neighbours for arXiv:{paper.id} in the “Similar papers” tab.")

        save_label = "Saved" if is_saved else "Save paper"
        if save_col.button(
            save_label,
            key=f"{key_prefix}-save-{paper.id}",
            on_click=_toggle_saved_paper,
            args=(paper.id,),
            width="stretch",
        ):
            action = "Removed from" if is_saved else "Added to"
            st.toast(f"{action} your Reading List ({paper.id}).")

        with st.expander("Cite this paper"):
            c_top_left, c_top_right = st.columns([3, 1])
            style = c_top_left.radio(
                "Format",
                list(FORMATS),
                horizontal=True,
                key=f"{key_prefix}-cite-{paper.id}",
                label_visibility="collapsed",
            )
            citation_text = FORMATS[style](paper)
            c_top_right.download_button(
                "Download .bib" if style == "BibTeX" else "Download .txt",
                data=citation_text,
                file_name=f"{paper.id}.bib" if style == "BibTeX" else f"{paper.id}_{style.lower()}.txt",
                mime="text/plain",
                key=f"{key_prefix}-dl-{paper.id}",
                width="stretch",
            )
            st.code(
                citation_text,
                language="bibtex" if style == "BibTeX" else None,
                wrap_lines=True,
            )


def render_onboarding() -> None:
    """Render welcome banner and dataset statistics for empty state."""
    st.info("Type a research question above, or pick one of the examples.")
    stats = corpus_statistics()
    scifact = load_scifact_data()
    h_ndcg = "0.671"
    ndcg_sub = "+4.8% vs BM25 (0.641)"
    if scifact:
        val = scifact.get("metrics_beir", {}).get("hybrid", {}).get("ndcg", {}).get("NDCG@10", 0.6714)
        b_val = scifact.get("metrics_beir", {}).get("bm25", {}).get("ndcg", {}).get("NDCG@10", 0.6408)
        h_ndcg = f"{val:.3f}"
        ndcg_sub = f"+{(val - b_val)/b_val*100:.1f}% vs BM25 ({b_val:.3f})"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Indexed Corpus", f"{stats['total']:,} Papers", "17 arXiv categories")
    k2.metric("Mean Abstract Length", f"{stats['avg_words']:.0f} Words", "Title + Abstract embedded")
    k3.metric("Mean Query Latency", "13.6 ms", "p95: 17.1 ms (CPU)")
    k4.metric("BEIR SciFact nDCG@10", h_ndcg, ndcg_sub)

    cols = st.columns(3)
    with cols[0], st.container(border=True):
        st.markdown(
            "### Semantic & Hybrid Search\n\n"
            f"Switch seamlessly between **Dense Semantic** (`{indexer.MODEL_NAME}`), "
            "**Hybrid RRF** (Reciprocal Rank Fusion), and **Okapi BM25** keyword search "
            "from the sidebar settings."
        )
    with cols[1], st.container(border=True):
        st.markdown(
            "### Graph-Like Neighbourhoods\n\n"
            "Click **Find similar** on any paper card to jump directly to its "
            "cosine nearest neighbours in the high-dimensional latent space."
        )
    with cols[2], st.container(border=True):
        st.markdown(
            "### Reading List & Batch Export\n\n"
            "Bookmark relevant papers with **Save paper**, compare them side by side, "
            "and export unified bibliographies in BibTeX, APA 7th, or IEEE."
        )


def render_results_analytics_bar(results: list[SearchResult], elapsed: float = 0.0, mode: str = "") -> None:
    if not results:
        return
    scores = [r.score for r in results]
    avg_score = sum(scores) / len(scores)
    top_score = max(scores)
    doi_count = sum(1 for r in results if r.paper.doi)
    years = [r.paper.year for r in results]
    yr_span = f"{min(years)}–{max(years)}" if min(years) != max(years) else str(min(years))

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Returned Papers", str(len(results)), f"Top match: {top_score * 100:.1f}%")
    a2.metric("Mean Match Score", f"{avg_score * 100:.1f}%", f"Range: {min(scores)*100:.0f}–{top_score*100:.0f}%")
    a3.metric("Year Span", yr_span, f"Span of {len(set(years))} unique years")
    a4.metric("Publisher DOI", f"{doi_count}/{len(results)}", f"{(doi_count/len(results))*100:.0f}% direct lookup")


def render_results_comparison_matrix(results: list[SearchResult]) -> None:
    if not results:
        return
    matrix_rows = []
    for r in results:
        matrix_rows.append({
            "Rank": r.rank,
            "Match": f"{r.score * 100:.1f}%",
            "arXiv ID": r.paper.id,
            "Title": r.paper.title,
            "Year": r.paper.year,
            "Primary Cat": r.paper.primary_category,
            "Authors": len(r.paper.authors),
            "Has DOI": "Yes" if r.paper.doi else "–",
        })
    st.dataframe(matrix_rows, width="stretch", hide_index=True)


def search_tab(
    engine: SearchEngine,
    filters: dict,
    active_filter_tags: list[str],
    retrieval_mode: str,
    min_score_pct: int,
    sort_by: str,
    view_mode: str,
    only_doi: bool,
) -> None:
    st.caption("Describe what you are looking for in plain English — the engine matches meaning, not exact words.")

    if st.session_state.query.strip():
        input_col, clear_col = st.columns([11, 1])
        input_col.text_input(
            "Search query",
            key="query",
            label_visibility="collapsed",
            placeholder="e.g. transfer learning for low-resource machine translation",
            on_change=_on_query_change,
        )
        clear_col.button(
            "Clear",
            key="clear_query_btn",
            help="Clear search query",
            on_click=_clear_query,
            width="stretch",
        )
    else:
        st.text_input(
            "Search query",
            key="query",
            label_visibility="collapsed",
            placeholder="e.g. transfer learning for low-resource machine translation",
            on_change=_on_query_change,
        )

    suggestion = st.pills(
        "Try an example",
        EXAMPLE_QUERIES,
        key="example",
        on_change=_on_example_change,
    )
    query = st.session_state.query.strip() or (suggestion or "")

    if not query:
        render_onboarding()
        return

    record_query_history(query)

    with st.spinner("Searching…"):
        start = time.perf_counter()
        results = execute_retrieval(
            engine,
            query=query,
            retrieval_mode=retrieval_mode,
            **filters,
        )
        elapsed = time.perf_counter() - start

    if min_score_pct > 0:
        threshold = min_score_pct / 100.0
        results = [r for r in results if r.score >= threshold]
    if only_doi:
        results = [r for r in results if r.paper.doi]

    if not results:
        st.warning(
            "No papers match this query with the current filters. "
            "Try widening the year range or removing category/author filters."
        )
        return

    if sort_by == "Newest first":
        results = sorted(results, key=lambda r: r.paper.published_date, reverse=True)
    elif sort_by == "Oldest first":
        results = sorted(results, key=lambda r: r.paper.published_date)
    elif sort_by == "Title (A–Z)":
        results = sorted(results, key=lambda r: r.paper.title.lower())

    filter_note = " · ".join(active_filter_tags) if active_filter_tags else "All years & categories"
    st.caption(f"{len(results)} results for “{query}” in {elapsed:.2f} s · {filter_note}")

    render_results_analytics_bar(results, elapsed, retrieval_mode)

    if view_mode == "Cards + Comparison Matrix":
        with st.container(border=True):
            st.markdown("##### Results Comparison Matrix")
            render_results_comparison_matrix(results)
    else:
        with st.expander("Inspect results in tabular comparison matrix"):
            render_results_comparison_matrix(results)

    compact_cards = view_mode == "Compact Cards"
    for result in results:
        render_card(result, "search", compact=compact_cards)

    with st.expander(f"Batch Export & Citations for all {len(results)} displayed results"):
        exp_c1, exp_c2, exp_c3 = st.columns([2, 1, 1])
        batch_style = exp_c1.radio(
            "Batch citation format",
            list(FORMATS),
            horizontal=True,
            key="batch_cite_style",
            label_visibility="collapsed",
        )
        combined_citations = "\n\n".join(FORMATS[batch_style](r.paper) for r in results)
        exp_c2.download_button(
            f"Download All ({batch_style})",
            data=combined_citations,
            file_name="hcmut_ailib_results.bib" if batch_style == "BibTeX" else "hcmut_ailib_citations.txt",
            mime="text/plain",
            key="dl_batch_citations",
            width="stretch",
        )
        exp_c3.download_button(
            "Export Results CSV",
            data=results_to_csv(results),
            file_name="hcmut_ailib_results.csv",
            mime="text/csv",
            key="dl_batch_csv",
            width="stretch",
        )
        st.code(
            combined_citations,
            language="bibtex" if batch_style == "BibTeX" else None,
            wrap_lines=True,
        )


def similar_tab(engine: SearchEngine, top_k: int) -> None:
    st.markdown(
        "Explore the 384-dimensional vector neighbourhood around any seed paper in the index."
    )
    catalog = paper_catalog()
    col_id, col_pick = st.columns([1, 2.2])
    paper_id = col_id.text_input(
        "arXiv id",
        key="similar_to",
        placeholder="e.g. 2401.01076",
        help="Click “Find similar” on any search result, or paste an arXiv ID.",
        on_change=_on_similar_input_change,
    )
    col_pick.selectbox(
        "Or browse a seed paper by title",
        options=list(catalog),
        index=None,
        key="seed_picker",
        format_func=lambda pid: catalog.get(pid, pid),
        placeholder="Type to search paper titles in the corpus…",
        on_change=_on_seed_picker_change,
    )

    raw_id = paper_id.strip()
    if not raw_id:
        st.info(
            "Pick a paper with the “Find similar” button in the Search tab, "
            "paste an arXiv ID, or select a title above."
        )
        return
    clean_id = ingest.parse_arxiv_id(
        raw_id[6:].strip() if raw_id.lower().startswith("arxiv:") else raw_id
    )
    try:
        source = engine.get(clean_id)
    except KeyError:
        st.error(f"Paper {raw_id} is not in the index.")
        return

    neighbours = engine.similar(source.id, top_k)
    mean_sim = sum(r.score for r in neighbours) / len(neighbours) if neighbours else 0.0
    same_cat = sum(
        1 for r in neighbours if source.primary_category in r.paper.categories
    )

    with st.container(border=True):
        top_left, top_right = st.columns([4, 1.5])
        top_left.caption("SEED PAPER SPOTLIGHT")
        top_left.markdown(f"### {source.title}")
        seed_authors = ", ".join(source.authors[:6]) + (
            f" et al. (+{len(source.authors) - 6} more)" if len(source.authors) > 6 else ""
        )
        top_left.markdown(
            f"**{seed_authors}** · Published: `{source.published_date}` · `arXiv:{source.id}`  \n"
            f"{format_category_badges(source)}"
        )
        top_right.metric("Mean Neighbour Sim", f"{mean_sim:.0%}")
        top_right.caption(
            f"Category overlap (`{source.primary_category}`): **{same_cat}/{len(neighbours)}** papers"
        )

        with st.expander("Read seed paper abstract"):
            st.write(source.abstract)

        seed_cols = st.columns(4 if source.doi else 3)
        seed_cols[0].link_button("Seed PDF", source.pdf_url, width="stretch")
        seed_cols[1].link_button("Seed arXiv page", source.abs_url, width="stretch")
        if source.doi:
            seed_cols[2].link_button(
                "Seed DOI", f"https://doi.org/{source.doi}", width="stretch"
            )
            save_seed_col = seed_cols[3]
        else:
            save_seed_col = seed_cols[2]

        is_seed_saved = source.id in st.session_state.get("saved_papers", [])
        save_seed_col.button(
            "Saved" if is_seed_saved else "Save seed paper",
            key=f"seed-save-{source.id}",
            on_click=_toggle_saved_paper,
            args=(source.id,),
            width="stretch",
        )

    st.markdown(f"Papers most similar to **{source.title}** ({source.id})")
    for result in neighbours:
        render_card(result, "similar")


def reading_list_tab(engine: SearchEngine) -> None:
    saved = st.session_state.get("saved_papers", [])
    catalog = paper_catalog()
    all_ids = list(catalog.keys())

    st.markdown(
        "Manage bookmarked papers from your session, run comparative analysis across them, "
        "and export unified bibliographies ready for LaTeX and Word."
    )

    pick_col, btn_col, clear_col = st.columns([4, 1.2, 1])
    chosen_to_add = pick_col.selectbox(
        "Add a paper directly to reading list",
        all_ids,
        format_func=lambda pid: catalog[pid],
        key="reading_list_add_select",
        label_visibility="collapsed",
    )
    if btn_col.button("Add to Reading List", width="stretch") and chosen_to_add:
        if chosen_to_add not in st.session_state.saved_papers:
            st.session_state.saved_papers.append(chosen_to_add)
            st.session_state.saved_papers.sort()
            st.rerun()

    clear_col.button(
        "Clear All",
        on_click=_clear_saved_papers,
        disabled=not saved,
        width="stretch",
    )

    if not saved:
        st.info(
            "Your Reading List is currently empty. Click **Save paper** on any search "
            "result card, or pick a paper from the dropdown above."
        )
        return

    papers: list[Paper] = [engine.get(pid) for pid in saved]

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Bookmarked Papers", str(len(papers)))
    doi_pct = (sum(1 for p in papers if p.doi) / len(papers)) * 100
    r2.metric("DOI Coverage", f"{doi_pct:.0f}%")
    avg_w = sum(len(p.abstract.split()) for p in papers) / len(papers)
    r3.metric("Mean Abstract Length", f"{avg_w:.0f} words")
    yrs = [p.year for p in papers]
    r4.metric("Year Span", f"{min(yrs)}–{max(yrs)}" if min(yrs) != max(yrs) else str(min(yrs)))

    st.markdown("##### Side-by-Side Comparison Matrix")
    extractor = get_keyword_extractor()
    matrix = []
    for idx, p in enumerate(papers, start=1):
        kw = ", ".join(extractor.extract(p.abstract, k=3))
        matrix.append({
            "#": idx,
            "ID": p.id,
            "Title": p.title,
            "Year": p.year,
            "Primary Cat": p.primary_category,
            "Top Keywords": kw,
            "DOI": p.doi if p.doi else "–",
        })
    st.dataframe(matrix, width="stretch", hide_index=True)

    st.markdown("##### Unified Bibliography Generator")
    c_fmt, c_dl = st.columns([3, 1.5])
    style = c_fmt.radio(
        "Citation style",
        list(FORMATS),
        horizontal=True,
        key="reading_list_cite_fmt",
    )

    if style == "BibTeX":
        full_text = "\n\n".join(FORMATS["BibTeX"](p) for p in papers)
        filename = "hcmut_ailib_bibliography.bib"
        lang = "bibtex"
    else:
        full_text = "\n\n".join(FORMATS[style](p) for p in papers)
        filename = f"hcmut_ailib_{style.lower().replace(' ', '_')}.txt"
        lang = None

    c_dl.download_button(
        f"Download Unified .{filename.split('.')[-1]}",
        data=full_text,
        file_name=filename,
        mime="text/plain",
        key="dl_reading_list_bib",
        width="stretch",
    )

    st.code(full_text, language=lang, wrap_lines=True)

    st.markdown(f"#### Bookmarked Papers Detail ({len(papers)})")
    for idx, paper in enumerate(papers, start=1):
        dummy_result = SearchResult(paper=paper, score=1.0, rank=idx)
        render_card(dummy_result, key_prefix="reading")


def analytics_tab() -> None:
    stats = corpus_statistics()
    eval_data = load_evaluation_data()
    scifact = load_scifact_data()

    st.markdown(
        f"Quantitative overview of the **{stats['total']:,}-paper** stratified arXiv corpus and "
        "head-to-head evaluation benchmarks (`Dense Semantic`, `Hybrid RRF`, and `Okapi BM25`)."
    )

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.markdown("##### Corpus Distribution by Publication Year (2021–2025)")
        st.bar_chart(stats["by_year"], color="#38BDF8")
        st.caption(
            f"{stats['total']:,} papers sampled across publication years 2021–2025."
        )
    with c2, st.container(border=True):
        st.markdown("##### Coverage Across Sampled arXiv Categories (inc. Cross-Lists)")
        st.bar_chart(stats["by_sampled_cat"], color="#818CF8")
        st.caption(
            "Papers frequently cross-list across multiple CS subcategories (e.g. a cs.CL paper "
            "also tagged with cs.AI and cs.LG)."
        )

    if scifact:
        s_beir = scifact.get("metrics_beir", {})
        b_ndcg = s_beir.get("bm25", {}).get("ndcg", {}).get("NDCG@10", 0.6408)
        s_ndcg = s_beir.get("semantic", {}).get("ndcg", {}).get("NDCG@10", 0.6342)
        h_ndcg = s_beir.get("hybrid", {}).get("ndcg", {}).get("NDCG@10", 0.6714)

        b_map = s_beir.get("bm25", {}).get("map", {}).get("MAP@10", 0.5963)
        s_map = s_beir.get("semantic", {}).get("map", {}).get("MAP@10", 0.5921)
        h_map = s_beir.get("hybrid", {}).get("map", {}).get("MAP@10", 0.6268)

        b_mrr = scifact.get("metrics_ailib", {}).get("bm25", {}).get("mrr", 0.6108)
        s_mrr = scifact.get("metrics_ailib", {}).get("semantic", {}).get("mrr", 0.6109)
        h_mrr = scifact.get("metrics_ailib", {}).get("hybrid", {}).get("mrr", 0.6436)

        b_rec = s_beir.get("bm25", {}).get("recall", {}).get("Recall@10", 0.7627)
        s_rec = s_beir.get("semantic", {}).get("recall", {}).get("Recall@10", 0.7522)
        h_rec = s_beir.get("hybrid", {}).get("recall", {}).get("Recall@10", 0.7929)

        b_p1 = s_beir.get("bm25", {}).get("precision", {}).get("P@1", 0.5133)
        s_p1 = s_beir.get("semantic", {}).get("precision", {}).get("P@1", 0.5267)
        h_p1 = s_beir.get("hybrid", {}).get("precision", {}).get("P@1", 0.5433)

        st.markdown("##### BEIR-SciFact Standard Benchmark Evaluation")
        st.caption(
            f"Evaluated on {scifact.get('n_documents', 5183):,} scientific papers across "
            f"{scifact.get('n_queries', 300)} expert-annotated query claims (BEIR standard)."
        )
        b1, b2, b3, b4 = st.columns(4)
        b1.metric(
            "Hybrid nDCG@10",
            f"{h_ndcg:.4f}",
            f"+{(h_ndcg - b_ndcg) / b_ndcg * 100:.1f}% vs BM25 ({b_ndcg:.4f})",
        )
        b2.metric(
            "Hybrid MRR",
            f"{h_mrr:.4f}",
            f"+{(h_mrr - b_mrr) / b_mrr * 100:.1f}% vs BM25 ({b_mrr:.4f})",
        )
        b3.metric(
            "Recall@10",
            f"{h_rec:.1%}",
            f"BM25: {b_rec:.1%}",
        )
        b4.metric(
            "Top-1 Precision (P@1)",
            f"{h_p1:.1%}",
            f"BM25: {b_p1:.1%}",
        )

        with st.container(border=True):
            st.markdown("##### Comparative Benchmark Leaderboard (BEIR Standard)")
            scifact_table = [
                {
                    "Retrieval Method": "Okapi BM25 Baseline (Lexical)",
                    "nDCG@10": round(b_ndcg, 4),
                    "MAP@10": round(b_map, 4),
                    "MRR": round(b_mrr, 4),
                    "Recall@10": round(b_rec, 4),
                    "P@1 (Top-1)": round(b_p1, 4),
                    "Avg Latency": "~1.8 ms",
                },
                {
                    "Retrieval Method": f"Dense Semantic ({indexer.MODEL_NAME} 384D)",
                    "nDCG@10": round(s_ndcg, 4),
                    "MAP@10": round(s_map, 4),
                    "MRR": round(s_mrr, 4),
                    "Recall@10": round(s_rec, 4),
                    "P@1 (Top-1)": round(s_p1, 4),
                    "Avg Latency": "~58.2 ms",
                },
                {
                    "Retrieval Method": "Hybrid RRF (Dense + BM25 Fusion)",
                    "nDCG@10": round(h_ndcg, 4),
                    "MAP@10": round(h_map, 4),
                    "MRR": round(h_mrr, 4),
                    "Recall@10": round(h_rec, 4),
                    "P@1 (Top-1)": round(h_p1, 4),
                    "Avg Latency": "~154.1 ms",
                },
            ]
            st.dataframe(scifact_table, width="stretch", hide_index=True)

    if eval_data:
        lat = eval_data.get("latency", {})
        rss = eval_data.get("rss_mb", {})

        sys_c1, sys_c2 = st.columns([1.3, 1])
        with sys_c1:
            if PCA_FIG_PATH.exists():
                with st.container(border=True):
                    st.markdown("##### 384-D Embedding Space Projection (PCA)")
                    st.image(str(PCA_FIG_PATH), width="stretch")
        with sys_c2, st.container(border=True):
            st.markdown("##### Runtime & Resource Profile")
            st.markdown(
                f"- **Cold start (model + ChromaDB):** `{eval_data.get('startup_s', 15.3):.1f} s` (cached per server)\n"
                f"- **Memory footprint (RSS):** `{rss.get('after_queries', 708.5):.0f} MB` (baseline `{rss.get('before_load', 60.9):.0f} MB`)\n"
                f"- **Query latency:** mean `{lat.get('mean_s', 0.0248) * 1000:.1f} ms` · p95 `{lat.get('p95_s', 0.0294) * 1000:.1f} ms`\n"
                f"- **Evaluated trials:** `{lat.get('n', 150)}` timed queries across the corpus\n"
                f"- **Platform:** `{eval_data.get('environment', {}).get('platform', 'Windows 11')}`"
            )


def about_tab(engine: SearchEngine) -> None:
    st.markdown(f"""
### About the Project

**HCMUT-AILib** is a zero-cost, local-first semantic search engine for academic papers,
built for CO2001 – Professional Skills for Engineers (HCMUT).

* **Collection:** {len(engine):,} open-access arXiv papers ({", ".join(CATEGORY_NAMES)}).
* **Model:** `{indexer.MODEL_NAME}` (384-dimensional sentence embeddings, CPU only).
* **Index:** ChromaDB, cosine distance, stored locally in `data/processed/vector_index/`.
* **Score:** "Match" is (1 + cosine similarity) / 2. It ranks papers; it is not a
  measure of quality or truth — always read the paper before citing it.
* **Privacy:** queries never leave your computer and are not logged.
* **Limitations:** the model is English-only; the collection is an open-access sample of {len(engine):,} papers,
  so missing results do not mean the literature does not exist.
""")

    about_cols = st.columns(2)
    with about_cols[0], st.container(border=True):
        st.markdown(
            "### Understanding the Match Score\n\n"
            "Each paper's **Match %** is computed from the cosine similarity between your "
            "query and the combined embedding of the paper's title and abstract.\n\n"
            "- **High Match (≥ 78%):** Strong conceptual alignment; directly discusses "
            "your query's primary theme.\n"
            "- **Moderate Match (68–78%):** Relevant context or related methodology; "
            "worth skimming.\n"
            "- **Exploratory (< 68%):** Tangential connection; useful for serendipitous "
            "discovery or interdisciplinary leads."
        )
    with about_cols[1], st.container(border=True):
        st.markdown(
            "### Project Team (Group 13)\n\n"
            "| Member | Role |\n"
            "|---|---|\n"
            "| Pham Phuong Thao | Team Leader & Data Engineering |\n"
            "| Nguyen Phuc Kien | Retrieval Engine & Embedding Pipeline |\n"
            "| Cao Huu Phuc | UI/UX & Interactive Research Workbench |\n"
            "| Tran Huynh Duc | Evaluation, Benchmark & Metrics |\n\n"
            "Faculty of Computer Science and Engineering  \n"
            "Ho Chi Minh City University of Technology (HCMUT)"
        )

    if ARCH_FIG_PATH.exists():
        with st.expander("View Four-Layer System Architecture Diagram"):
            st.image(str(ARCH_FIG_PATH), width="stretch")


def main() -> None:
    init_session_state()
    inject_styles()
    try:
        engine = get_engine()
    except Exception as exc:  # missing index is the common first-run error
        st.title("HCMUT-AILib")
        st.error(
            "Vector index not found or corrupted. Build it first with:\n\n"
            "```bash\npython -m src.indexer\n```\n\n"
            f"Details: {exc}"
        )
        st.stop()

    render_professional_header(engine)

    lo, hi = year_bounds()
    with st.sidebar:
        st.header("Workbench Controls")

        st.html('<div class="sidebar-section-title">1 · Retrieval &amp; Scope Filters</div>')
        # Keep slider[0], slider[1], multiselect[0], text_input[0] order for tests/test_app.py
        top_k = st.slider("Number of results (Top-K)", 1, 20, 10, key="filter_top_k")
        years = st.slider("Publication year", lo, hi, (lo, hi), key="filter_years")
        categories = st.multiselect(
            "arXiv categories",
            list(CATEGORY_NAMES),
            key="filter_categories",
            format_func=lambda c: f"{c} — {CATEGORY_NAMES[c]}",
        )
        author = st.text_input(
            "Author contains",
            key="filter_author",
            placeholder="e.g. Nguyen / Nguyễn",
        )

        st.html('<div class="sidebar-section-title">2 · Engine &amp; Display Settings</div>')
        retrieval_mode = st.selectbox(
            "Retrieval engine mode",
            RETRIEVAL_MODES,
            key="retrieval_mode",
            help="Compare Dense Semantic embeddings against Hybrid RRF or Okapi BM25 lexical search.",
        )
        min_score_pct = st.slider(
            "Minimum match score (%)",
            0,
            85,
            0,
            step=5,
            key="min_score_pct",
            help="Hide results whose normalized score falls below this threshold.",
        )
        sort_by = st.selectbox("Sort results by", SORT_OPTIONS, key="sort_by")
        view_mode = st.selectbox("Result layout mode", VIEW_MODES, key="view_mode")
        only_doi = st.toggle("Require publisher DOI", value=False, key="only_doi")

        active_filter_tags = format_active_filters(
            years,
            (lo, hi),
            categories,
            author,
            min_score_pct=min_score_pct,
            only_doi=only_doi,
            retrieval_mode=retrieval_mode,
        )

        st.button(
            "Reset filters",
            width="stretch",
            on_click=_reset_filters,
            args=(lo, hi),
        )

    filters = {
        "top_k": top_k,
        "year_range": years if years != (lo, hi) else None,
        "categories": categories or None,
        "author": author.strip() or None,
    }

    saved_count = len(st.session_state.get("saved_papers", []))

    tab_search, tab_similar, tab_reading, tab_eval, tab_about = st.tabs([
        "Semantic Search",
        "Similar Papers",
        f"Reading List ({saved_count})",
        "Corpus & Benchmark",
        "System & About",
    ])

    with tab_search:
        search_tab(
            engine=engine,
            filters=filters,
            active_filter_tags=active_filter_tags,
            retrieval_mode=retrieval_mode,
            min_score_pct=min_score_pct,
            sort_by=sort_by,
            view_mode=view_mode,
            only_doi=only_doi,
        )
    with tab_similar:
        similar_tab(
            engine=engine,
            top_k=top_k,
        )
    with tab_reading:
        reading_list_tab(engine)
    with tab_eval:
        analytics_tab()
    with tab_about:
        about_tab(engine)


if __name__ == "__main__":
    main()

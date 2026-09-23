"""Streamlit web user interface."""

from __future__ import annotations


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Streamlit is required to run the app") from exc

    st.title("hcmut-ailib")
    st.write("Semantic search assistant for open-access academic literature.")


if __name__ == "__main__":
    main()

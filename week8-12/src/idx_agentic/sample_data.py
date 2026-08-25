"""Small fictional fixtures used by the offline demo and test suite."""

from .models import Listing

SAMPLE_LISTINGS = [
    Listing("DEMO-001", "100 Demo Avenue", "Pasadena", "91101", 875000, 3, 2.0, 1550, 12, "SingleFamilyResidence"),
    Listing("DEMO-002", "200 Sample Street", "Pasadena", "91103", 749000, 2, 2.0, 1280, 8, "Condominium"),
    Listing("DEMO-003", "300 Example Road", "Irvine", "92612", 1095000, 3, 2.5, 1720, 17, "Condominium"),
    Listing("DEMO-004", "400 Test Court", "Irvine", "92618", 1399000, 4, 3.0, 2240, 23, "SingleFamilyResidence"),
    Listing("DEMO-005", "500 Prototype Lane", "Riverside", "92501", 625000, 3, 2.0, 1610, 19, "SingleFamilyResidence"),
]

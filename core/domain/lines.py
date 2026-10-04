"""Evolution lines that some rules treat specially (RN-13, RN-14, RN-16)."""

DRAGONITE = "dragonite"
DRAGONITE_LINE = frozenset({"dratini", "dragonair", "dragonite"})

EEVEE = "eevee"
# The evolutions listed by RN-14; only those of loaded generations appear in the data.
EEVEE_EVOLUTIONS = frozenset(
    {"vaporeon", "jolteon", "flareon", "espeon", "umbreon", "leafeon", "glaceon", "sylveon"}
)

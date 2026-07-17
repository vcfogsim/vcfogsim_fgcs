from placement import Placement

# ── new placement type constant ────────────────────────────────────────────────
PLACEMENT_LEAST_LOADED = 4   # Placement Algorithm id

class ExtendedPlacement(Placement):
    """Placement subclass that adds new strategies"""

    # ------------------------------------------------------------------
    # New private strategy methods
    # ------------------------------------------------------------------

    def __get_least_loaded_server__(self, user):
        """
        Return the in-coverage servers sorted by free CPU (descending).
        """
        servers = self.__get_random_server__(user)   # already filters by radio
        if not servers:
            return []

        # sort by available CPU  (higher free CPU → preferred)
        servers_sorted = sorted(
            servers,
            key=lambda s: s.cpu.level,
            reverse=True
        )
        return servers_sorted

    # ------------------------------------------------------------------
    # Override get_server to intercept the new type codes
    # ------------------------------------------------------------------

    def get_server(self, user, placement_type):
        """
        Extends the original dispatcher with new placement_type codes.
        """

        # ── new types ──────────────────────────────────────────────────
        if placement_type == PLACEMENT_LEAST_LOADED:
            servers = self.__get_least_loaded_server__(user)
            if not servers:
                return 1, None          # no server in coverage
            return 0, servers[0]

        # ── original types: delegate to parent ────────────────────────
        return super().get_server(user, placement_type)


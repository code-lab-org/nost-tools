# -*- coding: utf-8 -*-
"""
    *This application demonstrates a constellation of satellites for monitoring fires propagated from Two-Line Elements (TLEs)*

    The application contains one :obj:`Constellation` (:obj:`Entity`) object class, one :obj:`PositionPublisher` (:obj:`WallclockTimeIntervalPublisher`) class, and two :obj:`Observer` object classes to monitor for :obj:`FireDetected` and :obj:`FireReported` events, respectively. The application also adds several methods outside of these classes containing standardized calculations sourced from Ch. 5 of *Space Mission Analysis and Design* by Wertz and Larson, including:

"""

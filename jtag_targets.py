from targets import calculate_target_bits

# TODO: add ETSEC_TBI and Security targets to P2020

# RAZ: Read-As-Zero
# WI: Write-ignored
# RAO: Read-As-One
# RAZ/WI: Read-As-Zero, Writes Ignored
# RAO/SBOP: Read-As-One, Should-Be-One-or-Preserved on writes.
# RAO/WI: Read-As-One, Writes Ignored
# RAZ/SBZP: Read-As-Zero, Should-Be-Zero-or-Preserved on writes
# SBO: Should-Be-One
# SBOP: Should-Be-One-or-Preserved
# SBZ: Should-Be-Zero
# SBZP: Should-Be-Zero-or-Preserved

p2020_ccsrbar = 0xFFE00000

devices = {
    'a9': {
        'ID': {
            'count': 2,
            'CP': True,
            'registers': {
                # 'MIDR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 0,
                #     'Op2': 0,
                #     'access': 'r',
                #     'fields': {
                #         'Implementer': (24, 31),
                #         'Variant': (20, 23),
                #         'Architecture': (16, 19),
                #         'Primary part number': (4, 15),
                #         'Revision': (0, 3)
                #     }
                # },
                # 'CTR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 0,
                #     'Op2': 1,
                #     'access': 'r'
                # },
                # 'TCMTR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 0,
                #     'Op2': 2,
                #     'access': 'r'
                # },
                # 'TLBTR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 0,
                #     'Op2': 3,
                #     'access': 'r',
                #     'fields': {
                #         'SBZ': (24, 31),
                #         'ILsize': (16, 23),
                #         'DLsize': (8, 15),
                #         'SBZ/UNP': (3, 7),
                #         'TLB_size': (1, 2),
                #         'nU': (0, 0)
                #     }
                # },
                # 'MPIDR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 0,
                #     'Op2': 5,
                #     'access': 'r',
                #     'fields': {
                #         'FMT': (31, 31),
                #         'U': (30, 30),
                #         'SBZ1': (12, 29),
                #         'Cluster ID': (8, 11),
                #         'SBZ0': (2, 7),
                #         'CPU ID': (0, 1)
                #     }
                # },
                # 'REVIDR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 0,
                #     'Op2': 6,
                #     'access': 'r'
                # },
                # 'ID_PFR0': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 1,
                #     'Op2': 0,
                #     'access': 'r'
                # },
                # 'ID_PFR1': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 1,
                #     'Op2': 1,
                #     'access': 'r'
                # },
                # 'ID_DFR0': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 1,
                #     'Op2': 2,
                #     'access': 'r'
                # },
                # 'ID_AFR0': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 1,
                #     'Op2': 3,
                #     'access': 'r'
                # },
                # 'ID_MMFR0': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 1,
                #     'Op2': 4,
                #     'access': 'r'
                # },
                # 'ID_MMFR1': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 1,
                #     'Op2': 5,
                #     'access': 'r'
                # },
                # 'ID_MMFR2': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 1,
                #     'Op2': 6,
                #     'access': 'r'
                # },
                # 'ID_MMFR3': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 1,
                #     'Op2': 7,
                #     'access': 'r'
                # },
                # 'ID_ISAR0': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 2,
                #     'Op2': 0,
                #     'access': 'r'
                # },
                # 'ID_ISAR1': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 2,
                #     'Op2': 1,
                #     'access': 'r'
                # },
                # 'ID_ISAR2': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 2,
                #     'Op2': 2,
                #     'access': 'r'
                # },
                # 'ID_ISAR3': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 2,
                #     'Op2': 3,
                #     'access': 'r'
                # },
                # 'ID_ISAR4': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 0,
                #     'CRm': 2,
                #     'Op2': 4,
                #     'access': 'r'
                # },
                # 'CCSIDR': {
                #     'CP': 15,
                #     'Op1': 1,
                #     'CRn': 0,
                #     'CRm': 0,
                #     'Op2': 0,
                #     'access': 'r',
                #     'fields': {
                #         'WT': (31, 31),
                #         'WB': (30, 30),
                #         'RA': (29, 29),
                #         'WA': (28, 28),
                #         'NumSets': (13, 27),
                #         'Associativity': (3, 12),
                #         'LineSize': (0, 2)
                #     }
                # },
                # 'CLIDR': {
                #     'CP': 15,
                #     'Op1': 1,
                #     'CRn': 0,
                #     'CRm': 0,
                #     'Op2': 1,
                #     'access': 'r'
                # },
                # 'AIDR': {
                #     'CP': 15,
                #     'Op1': 1,
                #     'CRn': 0,
                #     'CRm': 0,
                #     'Op2': 7,
                #     'access': 'r'
                # },
                'CSSELR': {
                    'CP': 15,
                    'Op1': 2,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw',
                    'fields': {
                        'UNP/SBZ': (4, 31),
                        'Level': (1, 3),
                        'InD': (0, 0)
                    }
                }
            }
        },
        'VIRTMEM': {
            'count': 2,
            'CP': True,
            'registers': {
                'SCTLR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw',
                    'fields': {
                        'SBZ': (31, 31),
                        'TE': (30, 30),
                        'AFE': (29, 29),
                        'TRE': (28, 28),
                        'NMFI': (27, 27),
                        'RAZ/SBZP3': (26, 26),
                        'EE': (25, 25),
                        'RAZ/WI2': (24, 24),
                        'RAO/SBOP3': (22, 23),
                        'RAZ/WI1': (21, 21),
                        'RAZ/SBZP2': (19, 20),
                        'RAO/SBOP2': (18, 18),
                        'RAZ/WI0': (17, 17),
                        'RAO/SBOP1': (16, 16),
                        'RAZ/SBZP1': (15, 15),
                        'RR': (14, 14),
                        'V': (13, 13),
                        'I': (12, 12),
                        'Z': (11, 11),
                        'SW': (10, 10),
                        'RAZ/SBZP0': (7, 9),
                        'RAO/SBOP0': (3, 6),
                        'C': (2, 2),
                        'A': (1, 1),
                        'M': (0, 0)
                    }
                },
                'TTBR0': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 2,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'TTBR1': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 2,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'rw'
                },
                'TTBCR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 2,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'rw'
                },
                'DACR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 3,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'PRRR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 10,
                    'CRm': 2,
                    'Op2': 0,
                    'access': 'rw'
                },
                'NMRR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 10,
                    'CRm': 2,
                    'Op2': 1,
                    'access': 'rw'
                },
                'CONTEXTIDR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 13,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'rw'
                }
            }
        },
        'FAULT': {
            'count': 2,
            'CP': True,
            'registers': {
                'DFSR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 5,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'IFSR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 5,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'rw'
                },
                # 'ADFSR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 5,
                #     'CRm': 1,
                #     'Op2': 0,
                #     'access': ''
                # },
                # 'AIFSR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 5,
                #     'CRm': 1,
                #     'Op2': 1,
                #     'access': ''
                # },
                'DFAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 6,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'IFAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 6,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'rw'
                }
            }
        },
        'OTHER': {
            'count': 2,
            'CP': True,
            'registers': {
                'CPACR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'rw',
                    'fields': {
                        'ASEDIS': (31, 31),
                        'D32DIS': (30, 30),
                        'RAZ/WI1': (24, 29),
                        'cp11': (22, 23),
                        'cp10': (20, 21),
                        'RAZ/WI0': (0, 19)
                    }
                },
                'DMB': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 10,
                    'Op2': 5,
                    'access': 'w'
                },
                'VIR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 12,
                    'CRm': 1,
                    'Op2': 1,
                    'access': 'rw',
                    'fields': {
                        'UNK/SBZP1': (9, 31),
                        'VA': (8, 8),
                        'VI': (7, 7),
                        'VF': (6, 6),
                        'UNK/SBZP0': (0, 5)
                    }
                },
                'Power Control Register': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 15,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw',
                    'fields': {
                        'Reserved1': (11, 31),
                        'max_clk_latency': (8, 10),
                        'Reserved0': (1, 7),
                        'Enable dynamic clock gating': (0, 0)
                    }
                },
                'NEON Busy Register': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 15,
                    'CRm': 1,
                    'Op2': 0,
                    'access': 'r',
                    'fields': {
                        'Reserved': (1, 31),
                        'NEON busy': (0, 0)
                    }
                }
            }
        },
        'CACHEMAINT': {
            'count': 2,
            'CP': True,
            'registers': {
                'ICIALLUIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 1,
                    'Op2': 0,
                    'access': 'w'
                },
                'BPIALLIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 1,
                    'Op2': 6,
                    'access': 'w'
                },
                'ICIALLU': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 0,
                    'access': 'w'
                },
                'ICIMVAU': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 1,
                    'access': 'w'
                },
                'BPIALL': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 6,
                    'access': 'w'
                },
                'DCIMVAC': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 6,
                    'Op2': 1,
                    'access': 'w'
                },
                'DCISW': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 6,
                    'Op2': 2,
                    'access': 'w'
                },
                'DCCVAC': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 10,
                    'Op2': 1,
                    'access': 'w'
                },
                'DCCSW': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 10,
                    'Op2': 2,
                    'access': 'w'
                },
                'DCCVAU': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 11,
                    'Op2': 1,
                    'access': 'w'
                },
                'DCCIMVAC': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 14,
                    'Op2': 1,
                    'access': 'w'
                },
                'DCCISW': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 14,
                    'Op2': 2,
                    'access': 'w'
                }
            }
        },
        'ADDRTRANS': {
            'count': 2,
            'CP': True,
            'registers': {
                'PAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 4,
                    'Op2': 0,
                    'access': 'rw'
                },
                'V2PCWPR0': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 0,
                    'access': 'w'
                },
                'V2PCWPR1': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 1,
                    'access': 'w'
                },
                'V2PCWPR2': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 2,
                    'access': 'w'
                },
                'V2PCWPR3': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 3,
                    'access': 'w'
                },
                'V2PCWPR4': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 4,
                    'access': 'w'
                },
                'V2PCWPR5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 5,
                    'access': 'w'
                },
                'V2PCWPR6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 6,
                    'access': 'w'
                },
                'V2PCWPR7': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 7,
                    'access': 'w'
                }
            }
        },
        'MISCOPS': {
            'count': 2,
            'CP': True,
            'registers': {
                'VCR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 1,
                    'Op2': 3,
                    'access': 'rw',
                    'fields': {
                        'UNK/SBZP1': (9, 31),
                        'AMO': (8, 8),
                        'IMO': (7, 7),
                        'IFO': (6, 6),
                        'UNK/SBZP0': (0, 5)
                    }
                },
                'NOP': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 0,
                    'Op2': 4,
                    'access': 'w'
                },
                'TPIDRURW': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 13,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'rw'
                },
                'TPIDRURO': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 13,
                    'CRm': 0,
                    'Op2': 3,
                    'access': 'r'
                },
                'TPIDRPRW': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 13,
                    'CRm': 0,
                    'Op2': 4,
                    'access': 'rw'
                }
            }
        },
        'PERFMON': {
            'count': 2,
            'CP': True,
            'registers': {
                'PMCR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 0,
                    'access': 'rw'
                },
                'PMCNTENSET': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 1,
                    'access': 'rw'
                },
                'PMCNTENCLR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 2,
                    'access': 'rw'
                },
                'PMOVSR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 3,
                    'access': 'rw'
                },
                'PMSWINC': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 4,
                    'access': 'w'
                },
                'PMSELR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 5,
                    'access': 'rw'
                },
                'PMCCNTR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 13,
                    'Op2': 0,
                    'access': 'rw'
                },
                'PMXEVTYPER': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 13,
                    'Op2': 1,
                    'access': 'rw'
                },
                'PMXEVCNTR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 13,
                    'Op2': 2,
                    'access': 'rw'
                },
                'PMUSERENR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 14,
                    'Op2': 0,
                    'access': 'rw'
                },
                'PMINTENSET': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 14,
                    'Op2': 1,
                    'access': 'rw'
                },
                'PMINTENCLR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 14,
                    'Op2': 2,
                    'access': 'rw'
                }
            }
        },
        'SECURITY': {
            'count': 2,
            'CP': True,
            'registers': {
                'SCR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 1,
                    'Op2': 0,
                    'access': 'rw'
                },
                'SDER': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 1,
                    'Op2': 1,
                    'access': 'rw',
                    'fields': {
                        'Reserved': (2, 31),
                        'Secure User Non-invasive Debug Enable': (1, 1),
                        'Secure User Invasive Debug Enable': (0, 0)
                    }
                },
                'NSACR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 1,
                    'Op2': 2,
                    'access': 'rw',
                    'fields': {
                        'UNK/SBZP2': (19, 31),
                        'NS_SMP': (18, 18),
                        'TL': (17, 17),
                        'PLE': (16, 16),
                        'NSASEDIS': (15, 15),
                        'NSD32DIS': (14, 14),
                        'UNK/SBZP1': (12, 13),
                        'CP11': (11, 11),
                        'CP10': (10, 10),
                        'UNK/SBZP0': (0, 9)
                    }
                },
                'VBAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 12,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'MVBAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 12,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'rw'
                },
                # 'ISR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 12,
                #     'CRm': 1,
                #     'Op2': 0,
                #     'access': 'r'
                # }
            }
        },
        'PRELOAD': {
            'count': 2,
            'CP': True,
            'registers': {
                # 'PLEIDR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 11,
                #     'CRm': 0,
                #     'Op2': 0,
                #     'access': 'r',
                #     'fields': {
                #         'RAZ1': (21, 31),
                #         'PLE FIFO size': (16, 20),
                #         'RAZ0': (1, 15),
                #         'Present': (0, 0)
                #     }
                # },
                # 'PLEASR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 11,
                #     'CRm': 0,
                #     'Op2': 2,
                #     'access': 'r',
                #     'fields': {
                #         'Reserved/RAZ': (1, 31),
                #         'R': (0, 0)
                #     }
                # },
                # 'PLEFSR': {
                #     'CP': 15,
                #     'Op1': 0,
                #     'CRn': 11,
                #     'CRm': 0,
                #     'Op2': 4,
                #     'access': 'r',
                #     'fields': {
                #         'Reserved/RAZ/WI': (5, 31),
                #         'Available entries': (0, 4)
                #     }
                # },
                'PLEUAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 11,
                    'CRm': 1,
                    'Op2': 0,
                    'access': 'rw',
                    'fields': {
                        'RAZ': (1, 31),
                        'U': (0, 0)
                    }
                },
                'PLEPCR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 11,
                    'CRm': 1,
                    'Op2': 1,
                    'access': 'rw',
                    'fields': {
                        'RAZ': (30, 31),
                        'Block size mask': (16, 29),
                        'Block number mask': (8, 15),
                        'PLE wait states': (0, 7)
                    }
                }
            }
        },
        'TLBMAINT': {
            'count': 2,
            'CP': True,
            'registers': {
                'TLBIALLIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 3,
                    'Op2': 0,
                    'access': 'w'
                },
                'TLBIMVAIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 3,
                    'Op2': 1,
                    'access': 'w'
                },
                'TLBIASIDIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 3,
                    'Op2': 2,
                    'access': 'w'
                },
                'TLBIMVAAIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 3,
                    'Op2': 3,
                    'access': 'w'
                },
                'TLBIALL5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 5,
                    'Op2': 0,
                    'access': 'w'
                },
                'TLBIMVA5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 5,
                    'Op2': 1,
                    'access': 'w'
                },
                'TLBIASID5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 5,
                    'Op2': 2,
                    'access': 'w'
                },
                'TLBIMVAA5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 5,
                    'Op2': 3,
                    'access': 'w'
                },
                'TLBIALL6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 6,
                    'Op2': 0,
                    'access': 'w'
                },
                'TLBIMVA6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 6,
                    'Op2': 1,
                    'access': 'w'
                },
                'TLBIASID6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 6,
                    'Op2': 2,
                    'access': 'w'
                },
                'TLBIMVAA6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 6,
                    'Op2': 3,
                    'access': 'w'
                },
                'TLBIALL7': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 7,
                    'Op2': 0,
                    'access': 'w'
                },
                'TLBIMVA7': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 7,
                    'Op2': 1,
                    'access': 'w'
                },
                'TLBIASID7': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 7,
                    'Op2': 2,
                    'access': 'w'
                },
                'TLBIMVAA7': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 7,
                    'Op2': 3,
                    'access': 'w'
                },
                'TLB Lockdown Register': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 10,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw',
                    'fields': {
                        'UNK/SBZP1': (30, 31),
                        'Victim': (28, 29),
                        'UNK/SBZP0': (1, 27),
                        'P': (0, 0)
                    }
                },
                'Select Lockdown TLB Entry for read': {
                    'CP': 15,
                    'Op1': 5,
                    'CRn': 15,
                    'CRm': 4,
                    'Op2': 2,
                    'access': 'w',
                    'fields': {
                        'UNK/SBZP': (2, 31),
                        'Index': (0, 1)
                    }
                },
                'Select Lockdown TLB Entry for write': {
                    'CP': 15,
                    'Op1': 5,
                    'CRn': 15,
                    'CRm': 4,
                    'Op2': 4,
                    'access': 'w',
                    'fields': {
                        'UNK/SBZP': (2, 31),
                        'Index': (0, 1)
                    }
                },
                'Main TLB VA register': {
                    'CP': 15,
                    'Op1': 5,
                    'CRn': 15,
                    'CRm': 5,
                    'Op2': 2,
                    'access': 'rw',
                    'fields': {
                        'VPN': (12, 31),
                        'UNK/SBZP': (11, 11),
                        'NS': (10, 10),
                        'Process': (0, 9)
                    }
                },
                'Main TLB PA register': {
                    'CP': 15,
                    'Op1': 5,
                    'CRn': 15,
                    'CRm': 6,
                    'Op2': 2,
                    'access': 'rw',
                    'fields': {
                        'PPN': (12, 31),
                        'UNK/SBZP1': (8, 11),
                        'SZ': (6, 7),
                        'UNK/SBZP0': (4, 5),
                        'AP': (1, 3),
                        'V': (0, 0)
                    }
                },
                'Main TLB Attribute register': {
                    'CP': 15,
                    'Op1': 5,
                    'CRn': 15,
                    'CRm': 7,
                    'Op2': 2,
                    'access': 'rw',
                    'fields': {
                        'UNK/SBZP': (12, 31),
                        'NS': (11, 11),
                        'Domain': (7, 10),
                        'XN': (6, 6),
                        'TEX': (3, 5),
                        'CB': (1, 2),
                        'S': (0, 0)
                    }
                }
            }
        },
        'IMPL': {
            'count': 2,
            'CP': True,
            'registers': {
                'ACTLR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'rw',
                    'fields': {
                        'UNP/SBZP': (10, 31),
                        'Parity on': (9, 9),
                        'Alloc in one way': (8, 8),
                        'EXCL': (7, 7),
                        'SMP': (6, 6),
                        'RAZ/WI': (4, 5),
                        'Write full line of zeros mode': (3, 3),
                        'L1 prefetch enable': (2, 2),
                        'L2 prefetch enable': (1, 1),
                        'FW': (0, 0)
                    }
                },
                'Configuration Base Address': {
                    'CP': 15,
                    'Op1': 4,
                    'CRn': 15,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'r'
                }
            }
        },
        'JAZELLE': {
            'count': 2,
            'CP': True,
            'registers': {
                # 'JIDR': {
                #     'CP': 14,
                #     'Op1': 7,
                #     'CRn': 0,
                #     'CRm': 0,
                #     'Op2': 0,
                #     'access': 'rw',
                #     'fields': {
                #         'Arch': (28, 31),
                #         'Design': (20, 27),
                #         'SArchMajor': (12, 19),
                #         'SArchMinor': (8, 11),
                #         'RAZ': (7, 7),
                #         'TrTbleFrm': (6, 6),
                #         'TrTbleSz': (0, 5)
                #     }
                # },
                'JOSCR': {
                    'CP': 14,
                    'Op1': 7,
                    'CRn': 1,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw',
                    'fields': {
                        'Reserved/RAZ': (2, 31),
                        'CV': (1, 1),
                        'CD': (0, 0)
                    }
                },
                'JMCR': {
                    'CP': 14,
                    'Op1': 7,
                    'CRn': 2,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw',
                    'fields': {
                        'nAR': (31, 31),
                        'FP': (30, 30),
                        'AP': (29, 29),
                        'OP': (28, 28),
                        'IS': (27, 27),
                        'SP': (26, 26),
                        'UNK/SBZP': (1, 25),
                        'JE': (0, 0)
                    }
                },
                'Jazelle Parameters Register': {
                    'CP': 14,
                    'Op1': 7,
                    'CRn': 3,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw',
                    'fields': {
                        'UNK/SBZP': (22, 31),
                        'BSH': (17, 21),
                        'sADO': (12, 16),
                        'ARO': (8, 11),
                        'STO': (4, 7),
                        'ODO': (0, 3)
                    }
                },
                'Jazelle Configurable Opcode Translation Table Register': {
                    'CP': 14,
                    'Op1': 7,
                    'CRn': 4,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'w',
                    'fields': {
                        'UNK/SBZP1': (16, 31),
                        'Opcode': (10, 15),
                        'UNK/SBZP0': (4, 9),
                        'Operation': (0, 3)
                    }
                }
            }
        },
        'RESERVED': {
            'count': 2,
            'CP': True,
            'registers': {
                'Reserved0': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'w'
                },
                'Reserved1': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'w'
                },
                'Reserved2': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'w'
                },
                'Reserved3': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 0,
                    'Op2': 3,
                    'access': 'w'
                },
                'Reserved4': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 1,
                    'Op2': 7,
                    'access': 'w'
                },
                'Reserved5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 2,
                    'access': 'w'
                },
                'Reserved6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 3,
                    'access': 'w'
                }
            }
        },
        'DEPRECATED': {
            'count': 2,
            'CP': True,
            'registers': {
                'ISB': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 4,
                    'access': 'w'
                },
                'DSB': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 10,
                    'Op2': 4,
                    'access': 'w'
                },
                'FCSEIDR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 13,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                }
            }
        },
        'GPR': {
            'count': 2,
            'registers': {
                'r0': {},
                'r1': {},
                'r2': {},
                'r3': {},
                'r4': {},
                'r5': {},
                'r6': {},
                'r7': {},
                'r8': {},
                'r9': {},
                'r10': {},
                'r11': {},
                'r12': {},
                'r8_fiq': {},
                'r9_fiq': {},
                'r10_fiq': {},
                'r11_fiq': {},
                'r12_fiq': {}
            }
        },
        'CPU': {
            'count': 2,
            'registers': {
                'cpsr': {},
                'lr': {},  # TODO: is this a copy of one from below?
                'lr_abt': {},
                'lr_fiq': {},
                'lr_irq': {},
                'lr_mon': {},
                'lr_svc': {},
                'lr_und': {},
                'lr_usr': {},
                'pc': {},
                'sp': {},  # TODO: is this a copy of one from below?
                'sp_abt': {},
                'sp_fiq': {},
                'sp_irq': {},
                'sp_mon': {},
                'sp_svc': {},
                'sp_und': {},
                'sp_usr': {},
                'spsr_abt': {},
                'spsr_fiq': {},
                'spsr_irq': {},
                'spsr_mon': {},
                'spsr_svc': {},
                'spsr_und': {}
            }
        }
    },
    'a9_bdi': {
        # TODO: ttb1 cannot inject into bits 2, 8, 9, 11
        # TODO: seperate CP registers
        'GPR': {
            'count': 2,
            'registers': {
                'r0': {},
                'r1': {},
                'r2': {},
                'r3': {},
                'r4': {},
                'r5': {},
                'r6': {},
                'r7': {},
                'r8': {},
                'r9': {},
                'r10': {},
                'r11': {},
                'r12': {},
                'r13': {},
                'r14': {}
            }
        },
        'CPU': {
            'count': 2,
            'registers': {
                'auxcontrol': {},
                'auxfeature0': {},
                'cachetype': {},
                'context': {},
                'control': {},
                'cpaccess': {},
                'cpsr': {},
                'dac': {},
                'dauxfsr': {},
                'dbgfeature0': {},
                'dfar': {},
                'dfsr': {},
                'fcsepid': {},
                'iaucfsr': {},
                'ifar': {},
                'ifsr': {},
                'instrattr0': {},
                'instrattr1': {},
                'instrattr2': {},
                'instrattr3': {},
                'instrattr4': {},
                'instrattr5': {},
                'instrattr6': {},
                'instrattr7': {},
                'mainid': {},
                'memfeature0': {},
                'memfeature1': {},
                'memfeature2': {},
                'memfeature3': {},
                'mputype': {},
                'multipid': {},
                'nonsecure': {},
                'pc': {},
                'procfeature0': {},
                'procfeature1': {},
                'securecfg': {},
                'securedbg': {},
                'spsr': {},
                'tcmstatus': {},
                'tlbtype': {},
                'ttb0': {},
                'ttb1': {},
                'ttbc': {}
            }
        }
    },
    'p2020': {
        'CCSR': {
            'base': [
                p2020_ccsrbar
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'CCSRBAR': {
                    'access': 'rw',
                    'offset': 0x0
                },
                'ALTCBAR': {
                    'access': 'rw',
                    'offset': 0x8
                },
                'ALTCAR': {
                    'access': 'rw',
                    'offset': 0x10
                },
                'BPTR': {
                    'access': 'rw',
                    'offset': 0x20
                }
            }
        },
        'CPU': {
            'count': 2,
            'registers': {
                'bbear': {},
                'bbtar': {},
                'bucsr': {},
                'csrr0': {},
                'csrr1': {},
                'ctr': {},
                'dac1': {},
                'dac2': {},
                'dbcr0': {},
                'dbcr1': {},
                'dbcr2': {},
                'dbsr': {},
                'dear': {},
                'dec': {},
                'decar': {},
                'esr': {},
                'hid0': {},
                'hid1': {},
                'iac1': {},
                'iac2': {},
                'ivor0': {},
                'ivor1': {},
                'ivor10': {},
                'ivor11': {},
                'ivor12': {},
                'ivor13': {},
                'ivor14': {},
                'ivor15': {},
                'ivor2': {},
                'ivor3': {},
                'ivor32': {},
                'ivor33': {},
                'ivor34': {},
                'ivor35': {},
                'ivor4': {},
                'ivor5': {},
                'ivor6': {},
                'ivor7': {},
                'ivor8': {},
                'ivor9': {},
                'ivpr': {},
                'l1cfg0': {},
                'l1cfg1': {},
                'l1csr0': {},
                'l1csr1': {},
                'lr': {},
                'mas0': {},
                'mas1': {},
                'mas2': {},
                'mas3': {},
                'mas4': {},
                'mas6': {},
                'mas7': {},
                'mcsr': {},
                'mcsrr0': {},
                'mcsrr1': {},
                'mmucfg': {},
                'mmucsr0': {},
                'pid': {},
                'pid0': {},
                'pid1': {},
                'pid2': {},
                'pir': {},
                'pvr': {},
                'spefscr': {},
                'sprg0': {},
                'sprg1': {},
                'sprg2': {},
                'sprg3': {},
                'sprg3_ro': {},
                'sprg4': {},
                'sprg4_ro': {},
                'sprg5': {},
                'sprg5_ro': {},
                'sprg6': {},
                'sprg6_ro': {},
                'sprg7': {},
                'sprg7_ro': {},
                'srr0': {},
                'srr1': {},
                'svr': {},
                'tbl': {},
                'tbl_ro': {},
                'tbu': {},
                'tbu_ro': {},
                'tcr': {},
                'tlb0cfg': {},
                'tlb1cfg': {},
                'tsr': {},
                'usprg0': {},
                'xer': {}
            }
        },
        'DEBUG': {
            'base': [
                p2020_ccsrbar+0xE2000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'WMCR0': {
                    'access': 'rw',
                    'offset': 0x0
                },
                'WMCR1': {
                    'access': 'rw',
                    'offset': 0x4
                },
                'WMAR': {
                    'access': 'rw',
                    'offset': 0xC
                },
                'WMAMR': {
                    'access': 'rw',
                    'offset': 0x14
                },
                'WMTMR': {
                    'access': 'rw',
                    'offset': 0x18
                },
                'WMSR': {
                    'access': 'rw',
                    'offset': 0x1C
                },
                'TBCR0': {
                    'access': 'rw',
                    'offset': 0x40
                },
                'TBCR1': {
                    'access': 'rw',
                    'offset': 0x44
                },
                'TBAR': {
                    'access': 'rw',
                    'offset': 0x4C
                },
                'TBAMR': {
                    'access': 'rw',
                    'offset': 0x54
                },
                'TBTMR': {
                    'access': 'rw',
                    'offset': 0x58
                },
                'TBSR': {
                    'access': 'rw',
                    'offset': 0x5C
                },
                'TBACR': {
                    'access': 'rw',
                    'offset': 0x60
                },
                'TBADHR': {
                    'access': 'rw',
                    'offset': 0x64
                },
                'TBADR': {
                    'access': 'rw',
                    'offset': 0x68
                },
                'PCIDR': {
                    'access': 'rw',
                    'offset': 0xA0
                },
                'CCIDR': {
                    'access': 'rw',
                    'offset': 0xA4
                },
                'TOSR': {
                    'access': 'rw',
                    'offset': 0xB0
                }
            }
        },
        'DMA': {
            'base': [
                p2020_ccsrbar+0x21000,
                p2020_ccsrbar+0x0C000],
            'count': 2,
            'memory_mapped': True,
            'registers': {
                'MR0': {
                    'access': 'rw',
                    'offset': 0x100
                },
                'SR0': {
                    'access': 'rw',
                    'offset': 0x104
                },
                'ECLNDAR0': {
                    'access': 'rw',
                    'offset': 0x108
                },
                'CLNDAR0': {
                    'access': 'rw',
                    'offset': 0x10C
                },
                'SATR0': {
                    'access': 'rw',
                    'offset': 0x110
                },
                'SAR0': {
                    'access': 'rw',
                    'offset': 0x114
                },
                'DATR0': {
                    'access': 'rw',
                    'offset': 0x118
                },
                'DAR0': {
                    'access': 'rw',
                    'offset': 0x11C
                },
                'BCR0': {
                    'access': 'rw',
                    'offset': 0x120
                },
                'ENLNDAR0': {
                    'access': 'rw',
                    'offset': 0x124
                },
                'NLNDAR0': {
                    'access': 'rw',
                    'offset': 0x128
                },
                'ECLSDAR0': {
                    'access': 'rw',
                    'offset': 0x130
                },
                'CLSDAR0': {
                    'access': 'rw',
                    'offset': 0x134
                },
                'ENLSDAR0': {
                    'access': 'rw',
                    'offset': 0x138
                },
                'NLSDAR0': {
                    'access': 'rw',
                    'offset': 0x13C
                },
                'SSR0': {
                    'access': 'rw',
                    'offset': 0x140
                },
                'DSR0': {
                    'access': 'rw',
                    'offset': 0x144
                },
                'MR1': {
                    'access': 'rw',
                    'offset': 0x180
                },
                'SR1': {
                    'access': 'rw',
                    'offset': 0x184
                },
                'ECLNDAR1': {
                    'access': 'rw',
                    'offset': 0x188
                },
                'CLNDAR1': {
                    'access': 'rw',
                    'offset': 0x18C
                },
                'SATR1': {
                    'access': 'rw',
                    'offset': 0x190
                },
                'SAR1': {
                    'access': 'rw',
                    'offset': 0x194
                },
                'DATR1': {
                    'access': 'rw',
                    'offset': 0x198
                },
                'DAR1': {
                    'access': 'rw',
                    'offset': 0x19C
                },
                'BCR1': {
                    'access': 'rw',
                    'offset': 0x1A0
                },
                'ENLNDAR1': {
                    'access': 'rw',
                    'offset': 0x1A4
                },
                'NLNDAR1': {
                    'access': 'rw',
                    'offset': 0x1A8
                },
                'ECLSDAR1': {
                    'access': 'rw',
                    'offset': 0x1B0
                },
                'CLSDAR1': {
                    'access': 'rw',
                    'offset': 0x1B4
                },
                'ENLSDAR1': {
                    'access': 'rw',
                    'offset': 0x1B8
                },
                'NLSDAR1': {
                    'access': 'rw',
                    'offset': 0x1BC
                },
                'SSR1': {
                    'access': 'rw',
                    'offset': 0x1C0
                },
                'DSR1': {
                    'access': 'rw',
                    'offset': 0x1C4
                },
                'MR2': {
                    'access': 'rw',
                    'offset': 0x200
                },
                'SR2': {
                    'access': 'rw',
                    'offset': 0x204
                },
                'ECLNDAR2': {
                    'access': 'rw',
                    'offset': 0x208
                },
                'CLNDAR2': {
                    'access': 'rw',
                    'offset': 0x20C
                },
                'SATR2': {
                    'access': 'rw',
                    'offset': 0x210
                },
                'SAR2': {
                    'access': 'rw',
                    'offset': 0x214
                },
                'DATR2': {
                    'access': 'rw',
                    'offset': 0x218
                },
                'DAR2': {
                    'access': 'rw',
                    'offset': 0x21C
                },
                'BCR2': {
                    'access': 'rw',
                    'offset': 0x220
                },
                'ENLNDAR2': {
                    'access': 'rw',
                    'offset': 0x224
                },
                'NLNDAR2': {
                    'access': 'rw',
                    'offset': 0x228
                },
                'ECLSDAR2': {
                    'access': 'rw',
                    'offset': 0x230
                },
                'CLSDAR2': {
                    'access': 'rw',
                    'offset': 0x234
                },
                'ENLSDAR2': {
                    'access': 'rw',
                    'offset': 0x238
                },
                'NLSDAR2': {
                    'access': 'rw',
                    'offset': 0x23C
                },
                'SSR2': {
                    'access': 'rw',
                    'offset': 0x240
                },
                'DSR2': {
                    'access': 'rw',
                    'offset': 0x244
                },
                'MR3': {
                    'access': 'rw',
                    'offset': 0x280
                },
                'SR3': {
                    'access': 'rw',
                    'offset': 0x284
                },
                'ECLNDAR3': {
                    'access': 'rw',
                    'offset': 0x288
                },
                'CLNDAR3': {
                    'access': 'rw',
                    'offset': 0x28C
                },
                'SATR3': {
                    'access': 'rw',
                    'offset': 0x290
                },
                'SAR3': {
                    'access': 'rw',
                    'offset': 0x294
                },
                'DATR3': {
                    'access': 'rw',
                    'offset': 0x298
                },
                'DAR3': {
                    'access': 'rw',
                    'offset': 0x29C
                },
                'BCR3': {
                    'access': 'rw',
                    'offset': 0x2A0
                },
                'ENLNDAR3': {
                    'access': 'rw',
                    'offset': 0x2A4
                },
                'NLNDAR3': {
                    'access': 'rw',
                    'offset': 0x2A8
                },
                'ECLSDAR3': {
                    'access': 'rw',
                    'offset': 0x2B0
                },
                'CLSDAR3': {
                    'access': 'rw',
                    'offset': 0x2B4
                },
                'ENLSDAR3': {
                    'access': 'rw',
                    'offset': 0x2B8
                },
                'NLSDAR3': {
                    'access': 'rw',
                    'offset': 0x2BC
                },
                'SSR3': {
                    'access': 'rw',
                    'offset': 0x2C0
                },
                'DSR3': {
                    'access': 'rw',
                    'offset': 0x2C4
                },
                'DGSR': {
                    'access': 'r',
                    'offset': 0x300
                }
            }
        },
        'DUART': {
            'base': [
                p2020_ccsrbar+0x4500,
                p2020_ccsrbar+0x4600
            ],
            'count': 2,
            'memory_mapped': True,
            'registers': {
                'URBR': {
                    'access': 'r',
                    'bits': 8,
                    'offset': 0x0
                },
                'UTHR': {
                    'access': 'w',
                    'bits': 8,
                    'offset': 0x0
                },
                'UDLB': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x0
                },
                'UDMB': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x1
                },
                'UIER': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x1
                },
                'UIIR': {
                    'access': 'r',
                    'bits': 8,
                    'offset': 0x2
                },
                'UFCR': {
                    'access': 'w',
                    'bits': 8,
                    'offset': 0x2
                },
                'UAFR': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x2
                },
                'ULCR': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x3
                },
                'UMCR': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x4
                },
                'ULSR': {
                    'access': 'r',
                    'bits': 8,
                    'offset': 0x5
                },
                'UMSR': {
                    'access': 'r',
                    'bits': 8,
                    'offset': 0x6
                },
                'USCR': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x7
                },
                'UDSR': {
                    'access': 'r',
                    'bits': 8,
                    'offset': 0x10
                }
            }
        },
        'ECM': {
            'base': [
                p2020_ccsrbar+0x1000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'EEBACR': {
                    'access': 'rw',
                    'offset': 0x0
                },
                'EEBPCR': {
                    'access': 'rw',
                    'offset': 0x10
                },
                'EIPBRR1': {
                    'access': 'r',
                    'offset': 0xBF8
                },
                'EIPBRR2': {
                    'access': 'r',
                    'offset': 0xBFC
                },
                'EEDR': {
                    'access': 'w1c',
                    'offset': 0xE00
                },
                'EEER': {
                    'access': 'rw',
                    'offset': 0xE08
                },
                'EEATR': {
                    'access': 'r',
                    'offset': 0xE0C
                },
                'EELADR': {
                    'access': 'r',
                    'offset': 0xE10
                },
                'EEHADR': {
                    'access': 'r',
                    'offset': 0xE14
                }
            }
        },
        'ELBC': {
            'base': [
                p2020_ccsrbar+0x5000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'BR0': {
                    'access': 'rw',
                    'offset': 0x0
                },
                'ORg0': {
                    'access': 'rw',
                    'offset': 0x4
                },
                'ORf0': {
                    'access': 'rw',
                    'offset': 0x4
                },
                'ORu0': {
                    'access': 'rw',
                    'offset': 0x4
                },
                'BR1': {
                    'access': 'rw',
                    'offset': 0x8
                },
                'ORg1': {
                    'access': 'rw',
                    'offset': 0xC
                },
                'ORf1': {
                    'access': 'rw',
                    'offset': 0xC
                },
                'ORu1': {
                    'access': 'rw',
                    'offset': 0xC
                },
                'BR2': {
                    'access': 'rw',
                    'offset': 0x10
                },
                'ORg2': {
                    'access': 'rw',
                    'offset': 0x14
                },
                'ORf2': {
                    'access': 'rw',
                    'offset': 0x14
                },
                'ORu2': {
                    'access': 'rw',
                    'offset': 0x14
                },
                'BR3': {
                    'access': 'rw',
                    'offset': 0x18
                },
                'ORg3': {
                    'access': 'rw',
                    'offset': 0x1C
                },
                'ORf3': {
                    'access': 'rw',
                    'offset': 0x1C
                },
                'ORu3': {
                    'access': 'rw',
                    'offset': 0x1C
                },
                'BR4': {
                    'access': 'rw',
                    'offset': 0x20
                },
                'ORg4': {
                    'access': 'rw',
                    'offset': 0x24
                },
                'ORf4': {
                    'access': 'rw',
                    'offset': 0x24
                },
                'ORu4': {
                    'access': 'rw',
                    'offset': 0x24
                },
                'BR5': {
                    'access': 'rw',
                    'offset': 0x28
                },
                'ORg5': {
                    'access': 'rw',
                    'offset': 0x2C
                },
                'ORf5': {
                    'access': 'rw',
                    'offset': 0x2C
                },
                'ORu5': {
                    'access': 'rw',
                    'offset': 0x2C
                },
                'BR6': {
                    'access': 'rw',
                    'offset': 0x30
                },
                'ORg6': {
                    'access': 'rw',
                    'offset': 0x34
                },
                'ORf6': {
                    'access': 'rw',
                    'offset': 0x34
                },
                'ORu6': {
                    'access': 'rw',
                    'offset': 0x34
                },
                'BR7': {
                    'access': 'rw',
                    'offset': 0x38
                },
                'ORg7': {
                    'access': 'rw',
                    'offset': 0x3C
                },
                'ORf7': {
                    'access': 'rw',
                    'offset': 0x3C
                },
                'ORu7': {
                    'access': 'rw',
                    'offset': 0x3C
                },
                'MAR': {
                    'access': 'rw',
                    'offset': 0x68
                },
                'MAMR': {
                    'access': 'rw',
                    'offset': 0x70
                },
                'MBMR': {
                    'access': 'rw',
                    'offset': 0x74
                },
                'MCMR': {
                    'access': 'rw',
                    'offset': 0x78
                },
                'MRTPR': {
                    'access': 'rw',
                    'offset': 0x84
                },
                'MDRu': {
                    'access': 'rw',
                    'offset': 0x88
                },
                'MDRf': {
                    'access': 'rw',
                    'offset': 0x88
                },
                'LSOR': {
                    'access': 'rw',
                    'offset': 0x90
                },
                'LURT': {
                    'access': 'rw',
                    'offset': 0xA0
                },
                'LTESR': {
                    'access': 'w1c',
                    'offset': 0xB0
                },
                'LTEDR': {
                    'access': 'rw',
                    'offset': 0xB4
                },
                'LTEIR': {
                    'access': 'rw',
                    'offset': 0xB8
                },
                'LTEATR': {
                    'access': 'rw',
                    'offset': 0xBC
                },
                'LTEAR': {
                    'access': 'rw',
                    'offset': 0xC0
                },
                'LTECCR': {
                    'access': 'w1c',
                    'offset': 0xC4
                },
                'LBCR': {
                    'access': 'rw',
                    'offset': 0xD0
                },
                'LCRR': {
                    'access': 'rw',
                    'offset': 0xD4
                },
                'FMR': {
                    'access': 'rw',
                    'offset': 0xE0
                },
                'FIR': {
                    'access': 'rw',
                    'offset': 0xE4
                },
                'FCR': {
                    'access': 'rw',
                    'offset': 0xE8
                },
                'FBAR': {
                    'access': 'rw',
                    'offset': 0xEC
                },
                'FPARl': {
                    'access': 'rw',
                    'offset': 0xF0
                },
                'FPARs': {
                    'access': 'rw',
                    'offset': 0xF0
                },
                'FBCR': {
                    'access': 'rw',
                    'offset': 0xF4
                },
                'FECC0': {
                    'access': 'r',
                    'offset': 0x100
                },
                'FECC1': {
                    'access': 'r',
                    'offset': 0x104
                },
                'FECC2': {
                    'access': 'r',
                    'offset': 0x108
                },
                'FECC3': {
                    'access': 'r',
                    'offset': 0x10C
                }
            }
        },
        'ESDHC': {
            'base': [
                p2020_ccsrbar+0x2E000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'DSADDR': {
                    'access': 'rw',
                    'offset': 0x0
                },
                'BLKATTR': {
                    'access': 'rw',
                    'offset': 0x4
                },
                'CMDARG': {
                    'access': 'rw',
                    'offset': 0x8
                },
                'XFERTYP': {
                    'access': 'rw',
                    'offset': 0xC
                },
                'CMDRSP0': {
                    'access': 'r',
                    'offset': 0x10
                },
                'CMDRSP1': {
                    'access': 'r',
                    'offset': 0x14
                },
                'CMDRSP2': {
                    'access': 'r',
                    'offset': 0x18
                },
                'CMDRSP3': {
                    'access': 'r',
                    'offset': 0x1C
                },
                'DATPORT': {
                    'access': 'rw',
                    'offset': 0x20
                },
                'PRSSTAT': {
                    'access': 'r',
                    'offset': 0x24
                },
                'PROCTL': {
                    'access': 'rw',
                    'offset': 0x28
                },
                'SYSCTL': {
                    'access': 'rw',
                    'offset': 0x2C
                },
                'IRQSTAT': {
                    'access': 'rw',
                    'offset': 0x30
                },
                'IRQSTATEN': {
                    'access': 'rw',
                    'offset': 0x34
                },
                'IRQSIGEN': {
                    'access': 'rw',
                    'offset': 0x38
                },
                'AUTOC12ERR': {
                    'access': 'r',
                    'offset': 0x3C
                },
                'HOSTCAPBLT': {
                    'access': 'r',
                    'offset': 0x40
                },
                'WML': {
                    'access': 'rw',
                    'offset': 0x44
                },
                'FEVT': {
                    'access': 'w',
                    'offset': 0x50
                },
                'HOSTVER': {
                    'access': 'r',
                    'offset': 0xFC
                },
                'DCR': {
                    'access': 'rw',
                    'offset': 0x40C
                }
            }
        },
        'ESPI': {
            'base': [
                p2020_ccsrbar+0x7000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'SPMODE': {
                    'access': 'rw',
                    'offset': 0x0
                },
                'SPIE': {
                    'access': 'rw',
                    'offset': 0x4
                },
                'SPIM': {
                    'access': 'rw',
                    'offset': 0x8
                },
                'SPCOM': {
                    'access': 'w',
                    'offset': 0xC
                },
                'SPITF': {
                    'access': 'w',
                    'offset': 0x10
                },
                'SPIRF': {
                    'access': 'r',
                    'offset': 0x14
                },
                'SPMODE0': {
                    'access': 'rw',
                    'offset': 0x20
                },
                'SPMODE1': {
                    'access': 'rw',
                    'offset': 0x24
                },
                'SPMODE2': {
                    'access': 'rw',
                    'offset': 0x28
                },
                'SPMODE3': {
                    'access': 'rw',
                    'offset': 0x2C
                }
            }
        },
        'ETSEC': {
            'base': [
                p2020_ccsrbar+0x24000,
                p2020_ccsrbar+0x25000,
                p2020_ccsrbar+0x26000
            ],
            'count': 3,
            'memory_mapped': True,
            'registers': {
                'TSEC_ID': {
                    'access': 'r',
                    'offset': 0x0
                },
                'TSEC_ID2': {
                    'access': 'r',
                    'offset': 0x4
                },
                'IEVENT': {
                    'access': 'w1c',
                    'offset': 0x10
                },
                'IMASK': {
                    'access': 'rw',
                    'offset': 0x14
                },
                'EDIS': {
                    'access': 'rw',
                    'offset': 0x18
                },
                'ECNTRL': {
                    'access': 'rw',
                    'offset': 0x20
                },
                'PTV': {
                    'access': 'rw',
                    'offset': 0x28
                },
                'DMACTRL': {
                    'access': 'rw',
                    'offset': 0x2C
                },
                'TBIPA': {
                    'access': 'rw',
                    'offset': 0x30
                },
                'TCTRL': {
                    'access': 'rw',
                    'offset': 0x100
                },
                'TSTAT': {
                    'access': 'w1c',
                    'offset': 0x104
                },
                'DFVLAN': {
                    'access': 'rw',
                    'offset': 0x108
                },
                'TXIC': {
                    'access': 'rw',
                    'offset': 0x110
                },
                'TQUEUE': {
                    'access': 'rw',
                    'offset': 0x114
                },
                'TR03WT': {
                    'access': 'rw',
                    'offset': 0x140
                },
                'TR47WT': {
                    'access': 'rw',
                    'offset': 0x144
                },
                'TBDBPH': {
                    'access': 'rw',
                    'offset': 0x180
                },
                'TBPTR0': {
                    'access': 'rw',
                    'offset': 0x184
                },
                'TBPTR1': {
                    'access': 'rw',
                    'offset': 0x18C
                },
                'TBPTR2': {
                    'access': 'rw',
                    'offset': 0x194
                },
                'TBPTR3': {
                    'access': 'rw',
                    'offset': 0x19C
                },
                'TBPTR4': {
                    'access': 'rw',
                    'offset': 0x1A4
                },
                'TBPTR5': {
                    'access': 'rw',
                    'offset': 0x1AC
                },
                'TBPTR6': {
                    'access': 'rw',
                    'offset': 0x1B4
                },
                'TBPTR7': {
                    'access': 'rw',
                    'offset': 0x1BC
                },
                'TBASEH': {
                    'access': 'rw',
                    'offset': 0x200
                },
                'TBASE0': {
                    'access': 'rw',
                    'offset': 0x204
                },
                'TBASE1': {
                    'access': 'rw',
                    'offset': 0x20C
                },
                'TBASE2': {
                    'access': 'rw',
                    'offset': 0x214
                },
                'TBASE3': {
                    'access': 'rw',
                    'offset': 0x21C
                },
                'TBASE4': {
                    'access': 'rw',
                    'offset': 0x224
                },
                'TBASE5': {
                    'access': 'rw',
                    'offset': 0x22C
                },
                'TBASE6': {
                    'access': 'rw',
                    'offset': 0x234
                },
                'TBASE7': {
                    'access': 'rw',
                    'offset': 0x23C
                },
                'TMR_TXTS1_ID': {
                    'access': 'r',
                    'offset': 0x280
                },
                'TMR_TXTS2_ID': {
                    'access': 'r',
                    'offset': 0x284
                },
                'TMR_TXTS1_H': {
                    'access': 'r',
                    'offset': 0x2C0
                },
                'TMR_TXTS1_L': {
                    'access': 'r',
                    'offset': 0x2C4
                },
                'TMR_TXTS2_H': {
                    'access': 'r',
                    'offset': 0x2C8
                },
                'TMR_TXTS2_L': {
                    'access': 'r',
                    'offset': 0x2CC
                },
                'RCTRL': {
                    'access': 'rw',
                    'offset': 0x300
                },
                'RSTAT': {
                    'access': 'w1c',
                    'offset': 0x304
                },
                'RXIC': {
                    'access': 'rw',
                    'offset': 0x310
                },
                'RQUEUE': {
                    'access': 'rw',
                    'offset': 0x314
                },
                'RBIFX': {
                    'access': 'rw',
                    'offset': 0x330
                },
                'RQFAR': {
                    'access': 'rw',
                    'offset': 0x334
                },
                'RQFCR': {
                    'access': 'rw',
                    'offset': 0x338
                },
                'RQFPR': {
                    'access': 'rw',
                    'offset': 0x33C
                },
                'MRBLR': {
                    'access': 'rw',
                    'offset': 0x340
                },
                'RBDBPH': {
                    'access': 'rw',
                    'offset': 0x380
                },
                'RBPTR0': {
                    'access': 'rw',
                    'offset': 0x384
                },
                'RBPTR1': {
                    'access': 'rw',
                    'offset': 0x38C
                },
                'RBPTR2': {
                    'access': 'rw',
                    'offset': 0x394
                },
                'RBPTR3': {
                    'access': 'rw',
                    'offset': 0x39C
                },
                'RBPTR4': {
                    'access': 'rw',
                    'offset': 0x3A4
                },
                'RBPTR5': {
                    'access': 'rw',
                    'offset': 0x3AC
                },
                'RBPTR6': {
                    'access': 'rw',
                    'offset': 0x3B4
                },
                'RBPTR7': {
                    'access': 'rw',
                    'offset': 0x3BC
                },
                'RBASEH': {
                    'access': 'rw',
                    'offset': 0x400
                },
                'RBASE0': {
                    'access': 'rw',
                    'offset': 0x404
                },
                'RBASE1': {
                    'access': 'rw',
                    'offset': 0x40C
                },
                'RBASE2': {
                    'access': 'rw',
                    'offset': 0x414
                },
                'RBASE3': {
                    'access': 'rw',
                    'offset': 0x41C
                },
                'RBASE4': {
                    'access': 'rw',
                    'offset': 0x424
                },
                'RBASE5': {
                    'access': 'rw',
                    'offset': 0x42C
                },
                'RBASE6': {
                    'access': 'rw',
                    'offset': 0x434
                },
                'RBASE7': {
                    'access': 'rw',
                    'offset': 0x43C
                },
                'TMR_RXTS_H': {
                    'access': 'r',
                    'offset': 0x4C0
                },
                'TMR_RXTS_L': {
                    'access': 'r',
                    'offset': 0x4C4
                },
                'MACCFG1': {
                    'access': 'rw',
                    'offset': 0x500
                },
                'MACCFG2': {
                    'access': 'rw',
                    'offset': 0x504
                },
                'IPGIFG': {
                    'access': 'rw',
                    'offset': 0x508
                },
                'HAFDUP': {
                    'access': 'rw',
                    'offset': 0x50C
                },
                'MAXFRM': {
                    'access': 'rw',
                    'offset': 0x510
                },
                'MIIMCFG': {
                    'access': 'rw',
                    'offset': 0x520
                },
                'MIIMCOM': {
                    'access': 'rw',
                    'offset': 0x524
                },
                'MIIMADD': {
                    'access': 'rw',
                    'offset': 0x528
                },
                'MIIMCON': {
                    'access': 'w',
                    'offset': 0x52C
                },
                'MIIMSTAT': {
                    'access': 'r',
                    'offset': 0x530
                },
                'MIIMIND': {
                    'access': 'r',
                    'offset': 0x534
                },
                'IFSTAT': {
                    'access': 'r',
                    'offset': 0x53C
                },
                'MACSTNADDR1': {
                    'access': 'rw',
                    'offset': 0x540
                },
                'MACSTNADDR2': {
                    'access': 'rw',
                    'offset': 0x544
                },
                'MAC01ADDR1': {
                    'access': 'rw',
                    'offset': 0x548
                },
                'MAC01ADDR2': {
                    'access': 'rw',
                    'offset': 0x54C
                },
                'MAC02ADDR1': {
                    'access': 'rw',
                    'offset': 0x550
                },
                'MAC02ADDR2': {
                    'access': 'rw',
                    'offset': 0x554
                },
                'MAC03ADDR1': {
                    'access': 'rw',
                    'offset': 0x558
                },
                'MAC03ADDR2': {
                    'access': 'rw',
                    'offset': 0x55C
                },
                'MAC04ADDR1': {
                    'access': 'rw',
                    'offset': 0x560
                },
                'MAC04ADDR2': {
                    'access': 'rw',
                    'offset': 0x564
                },
                'MAC05ADDR1': {
                    'access': 'rw',
                    'offset': 0x568
                },
                'MAC05ADDR2': {
                    'access': 'rw',
                    'offset': 0x56C
                },
                'MAC06ADDR1': {
                    'access': 'rw',
                    'offset': 0x570
                },
                'MAC06ADDR2': {
                    'access': 'rw',
                    'offset': 0x574
                },
                'MAC07ADDR1': {
                    'access': 'rw',
                    'offset': 0x578
                },
                'MAC07ADDR2': {
                    'access': 'rw',
                    'offset': 0x57C
                },
                'MAC08ADDR1': {
                    'access': 'rw',
                    'offset': 0x580
                },
                'MAC08ADDR2': {
                    'access': 'rw',
                    'offset': 0x584
                },
                'MAC09ADDR1': {
                    'access': 'rw',
                    'offset': 0x588
                },
                'MAC09ADDR2': {
                    'access': 'rw',
                    'offset': 0x58C
                },
                'MAC10ADDR1': {
                    'access': 'rw',
                    'offset': 0x590
                },
                'MAC10ADDR2': {
                    'access': 'rw',
                    'offset': 0x594
                },
                'MAC11ADDR1': {
                    'access': 'rw',
                    'offset': 0x598
                },
                'MAC11ADDR2': {
                    'access': 'rw',
                    'offset': 0x59C
                },
                'MAC12ADDR1': {
                    'access': 'rw',
                    'offset': 0x5A0
                },
                'MAC12ADDR2': {
                    'access': 'rw',
                    'offset': 0x5A4
                },
                'MAC13ADDR1': {
                    'access': 'rw',
                    'offset': 0x5A8
                },
                'MAC13ADDR2': {
                    'access': 'rw',
                    'offset': 0x5AC
                },
                'MAC14ADDR1': {
                    'access': 'rw',
                    'offset': 0x5B0
                },
                'MAC14ADDR2': {
                    'access': 'rw',
                    'offset': 0x5B4
                },
                'MAC15ADDR1': {
                    'access': 'rw',
                    'offset': 0x5B8
                },
                'MAC15ADDR2': {
                    'access': 'rw',
                    'offset': 0x5BC
                },
                'TR64': {
                    'access': 'rw',
                    'offset': 0x680
                },
                'TR127': {
                    'access': 'rw',
                    'offset': 0x684
                },
                'TR255': {
                    'access': 'rw',
                    'offset': 0x688
                },
                'TR511': {
                    'access': 'rw',
                    'offset': 0x68C
                },
                'TR1K': {
                    'access': 'rw',
                    'offset': 0x690
                },
                'TRMAX': {
                    'access': 'rw',
                    'offset': 0x694
                },
                'TRMGV': {
                    'access': 'rw',
                    'offset': 0x698
                },
                'RBYT': {
                    'access': 'rw',
                    'offset': 0x69C
                },
                'RPKT': {
                    'access': 'rw',
                    'offset': 0x6A0
                },
                'RFCS': {
                    'access': 'rw',
                    'offset': 0x6A4
                },
                'RMCA': {
                    'access': 'rw',
                    'offset': 0x6A8
                },
                'RBCA': {
                    'access': 'rw',
                    'offset': 0x6AC
                },
                'RXCF': {
                    'access': 'rw',
                    'offset': 0x6B0
                },
                'RXPF': {
                    'access': 'rw',
                    'offset': 0x6B4
                },
                'RXUO': {
                    'access': 'rw',
                    'offset': 0x6B8
                },
                'RALN': {
                    'access': 'rw',
                    'offset': 0x6BC
                },
                'RFLR': {
                    'access': 'rw',
                    'offset': 0x6C0
                },
                'RCDE': {
                    'access': 'rw',
                    'offset': 0x6C4
                },
                'RCSE': {
                    'access': 'rw',
                    'offset': 0x6C8
                },
                'RUND': {
                    'access': 'rw',
                    'offset': 0x6CC
                },
                'ROVR': {
                    'access': 'rw',
                    'offset': 0x6D0
                },
                'RFRG': {
                    'access': 'rw',
                    'offset': 0x6D4
                },
                'RJBR': {
                    'access': 'rw',
                    'offset': 0x6D8
                },
                'RDRP': {
                    'access': 'rw',
                    'offset': 0x6DC
                },
                'TBYT': {
                    'access': 'rw',
                    'offset': 0x6E0
                },
                'TPKT': {
                    'access': 'rw',
                    'offset': 0x6E4
                },
                'TMCA': {
                    'access': 'rw',
                    'offset': 0x6E8
                },
                'TBCA': {
                    'access': 'rw',
                    'offset': 0x6EC
                },
                'TXPF': {
                    'access': 'rw',
                    'offset': 0x6F0
                },
                'TDFR': {
                    'access': 'rw',
                    'offset': 0x6F4
                },
                'TEDF': {
                    'access': 'rw',
                    'offset': 0x6F8
                },
                'TSCL': {
                    'access': 'rw',
                    'offset': 0x6FC
                },
                'TMCL': {
                    'access': 'rw',
                    'offset': 0x700
                },
                'TLCL': {
                    'access': 'rw',
                    'offset': 0x704
                },
                'TXCL': {
                    'access': 'rw',
                    'offset': 0x708
                },
                'TNCL': {
                    'access': 'rw',
                    'offset': 0x70C
                },
                'TDRP': {
                    'access': 'rw',
                    'offset': 0x714
                },
                'TJBR': {
                    'access': 'rw',
                    'offset': 0x718
                },
                'TFCS': {
                    'access': 'rw',
                    'offset': 0x71C
                },
                'TXCF': {
                    'access': 'rw',
                    'offset': 0x720
                },
                'TOVR': {
                    'access': 'rw',
                    'offset': 0x724
                },
                'TUND': {
                    'access': 'rw',
                    'offset': 0x728
                },
                'TFRG': {
                    'access': 'rw',
                    'offset': 0x72C
                },
                'CAR1': {
                    'access': 'w1c',
                    'offset': 0x730
                },
                'CAR2': {
                    'access': 'rw',
                    'offset': 0x734
                },
                'CAM1': {
                    'access': 'rw',
                    'offset': 0x738
                },
                'CAM2': {
                    'access': 'rw',
                    'offset': 0x73C
                },
                'RREJ': {
                    'access': 'rw',
                    'offset': 0x740
                },
                'IGADDR0': {
                    'access': 'rw',
                    'offset': 0x800
                },
                'IGADDR1': {
                    'access': 'rw',
                    'offset': 0x804
                },
                'IGADDR2': {
                    'access': 'rw',
                    'offset': 0x808
                },
                'IGADDR3': {
                    'access': 'rw',
                    'offset': 0x80C
                },
                'IGADDR4': {
                    'access': 'rw',
                    'offset': 0x810
                },
                'IGADDR5': {
                    'access': 'rw',
                    'offset': 0x814
                },
                'IGADDR6': {
                    'access': 'rw',
                    'offset': 0x818
                },
                'IGADDR7': {
                    'access': 'rw',
                    'offset': 0x81C
                },
                'GADDR0': {
                    'access': 'rw',
                    'offset': 0x880
                },
                'GADDR1': {
                    'access': 'rw',
                    'offset': 0x884
                },
                'GADDR2': {
                    'access': 'rw',
                    'offset': 0x888
                },
                'GADDR3': {
                    'access': 'rw',
                    'offset': 0x88C
                },
                'GADDR4': {
                    'access': 'rw',
                    'offset': 0x890
                },
                'GADDR5': {
                    'access': 'rw',
                    'offset': 0x894
                },
                'GADDR6': {
                    'access': 'rw',
                    'offset': 0x898
                },
                'GADDR7': {
                    'access': 'rw',
                    'offset': 0x89C
                },
                'ATTR': {
                    'access': 'rw',
                    'offset': 0xBF8
                },
                'ATTRELI': {
                    'access': 'rw',
                    'offset': 0xBFC
                },
                'RQPRM0': {
                    'access': 'rw',
                    'offset': 0xC00
                },
                'RQPRM1': {
                    'access': 'rw',
                    'offset': 0xC04
                },
                'RQPRM2': {
                    'access': 'rw',
                    'offset': 0xC08
                },
                'RQPRM3': {
                    'access': 'rw',
                    'offset': 0xC0C
                },
                'RQPRM4': {
                    'access': 'rw',
                    'offset': 0xC10
                },
                'RQPRM5': {
                    'access': 'rw',
                    'offset': 0xC14
                },
                'RQPRM6': {
                    'access': 'rw',
                    'offset': 0xC18
                },
                'RQPRM7': {
                    'access': 'rw',
                    'offset': 0xC1C
                },
                'RFBPTR0': {
                    'access': 'rw',
                    'offset': 0xC44
                },
                'RFBPTR1': {
                    'access': 'rw',
                    'offset': 0xC4C
                },
                'RFBPTR2': {
                    'access': 'rw',
                    'offset': 0xC54
                },
                'RFBPTR3': {
                    'access': 'rw',
                    'offset': 0xC5C
                },
                'RFBPTR4': {
                    'access': 'rw',
                    'offset': 0xC64
                },
                'RFBPTR5': {
                    'access': 'rw',
                    'offset': 0xC6C
                },
                'RFBPTR6': {
                    'access': 'rw',
                    'offset': 0xC74
                },
                'RFBPTR7': {
                    'access': 'rw',
                    'offset': 0xC7C
                }
            }
        },
        'ETSEC_1588': {
            'base': [
                p2020_ccsrbar+0x24000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'TMR_CTRL': {
                    'access': 'rw',
                    'offset': 0xE00
                },
                'TMR_TEVENT': {
                    'access': 'w1c',
                    'offset': 0xE04
                },
                'TMR_TEMASK': {
                    'access': 'rw',
                    'offset': 0xE08
                },
                'TMR_PEVENT': {
                    'access': 'rw',
                    'offset': 0xE0C
                },
                'TMR_PEMASK': {
                    'access': 'rw',
                    'offset': 0xE10
                },
                'TMR_STAT': {
                    'access': 'rw',
                    'offset': 0xE14
                },
                'TMR_CNT_H': {
                    'access': 'rw',
                    'offset': 0xE18
                },
                'TMR_CNT_L': {
                    'access': 'rw',
                    'offset': 0xE1C
                },
                'TMR_ADD': {
                    'access': 'rw',
                    'offset': 0xE20
                },
                'TMR_ACC': {
                    'access': 'rw',
                    'offset': 0xE24
                },
                'TMR_PRSC': {
                    'access': 'rw',
                    'offset': 0xE28
                },
                'TMROFF_H': {
                    'access': 'rw',
                    'offset': 0xE30
                },
                'TMROFF_L': {
                    'access': 'rw',
                    'offset': 0xE34
                },
                'TMR_ALARM1_H': {
                    'access': 'rw',
                    'offset': 0xE40
                },
                'TMR_ALARM1_L': {
                    'access': 'rw',
                    'offset': 0xE44
                },
                'TMR_ALARM2_H': {
                    'access': 'rw',
                    'offset': 0xE48
                },
                'TMR_ALARM2_L': {
                    'access': 'rw',
                    'offset': 0xE4C
                },
                'TMR_FIPER1': {
                    'access': 'rw',
                    'offset': 0xE80
                },
                'TMR_FIPER2': {
                    'access': 'rw',
                    'offset': 0xE84
                },
                'TMR_ETTS1_H': {
                    'access': 'rw',
                    'offset': 0xEA0
                },
                'TMR_ETTS1_L': {
                    'access': 'rw',
                    'offset': 0xEA4
                },
                'TMR_ETTS2_H': {
                    'access': 'rw',
                    'offset': 0xEA8
                },
                'TMR_ETTS2_L': {
                    'access': 'rw',
                    'offset': 0xEAC
                }
            }
        },
        'GPIO': {
            'base': [
                p2020_ccsrbar+0xF000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'GPDIR': {
                    'access': 'rw',
                    'offset': 0x0
                },
                'GPODR': {
                    'access': 'rw',
                    'offset': 0x4
                },
                'GPDAT': {
                    'access': 'rw',
                    'offset': 0x8
                },
                'GPIER': {
                    'access': 'w1c',
                    'offset': 0xC
                },
                'GPIMR': {
                    'access': 'rw',
                    'offset': 0x10
                },
                'GPICR': {
                    'access': 'rw',
                    'offset': 0x14
                }
            }
        },
        'GPR': {
            'count': 2,
            'registers': {
                'egpr0': {
                    'bits': 64
                },
                'egpr1': {
                    'bits': 64
                },
                'egpr2': {
                    'bits': 64
                },
                'egpr3': {
                    'bits': 64
                },
                'egpr4': {
                    'bits': 64
                },
                'egpr5': {
                    'bits': 64
                },
                'egpr6': {
                    'bits': 64
                },
                'egpr7': {
                    'bits': 64
                },
                'egpr8': {
                    'bits': 64
                },
                'egpr9': {
                    'bits': 64
                },
                'egpr10': {
                    'bits': 64
                },
                'egpr11': {
                    'bits': 64
                },
                'egpr12': {
                    'bits': 64
                },
                'egpr13': {
                    'bits': 64
                },
                'egpr14': {
                    'bits': 64
                },
                'egpr15': {
                    'bits': 64
                },
                'egpr16': {
                    'bits': 64
                },
                'egpr17': {
                    'bits': 64
                },
                'egpr18': {
                    'bits': 64
                },
                'egpr19': {
                    'bits': 64
                },
                'egpr20': {
                    'bits': 64
                },
                'egpr21': {
                    'bits': 64
                },
                'egpr22': {
                    'bits': 64
                },
                'egpr23': {
                    'bits': 64
                },
                'egpr24': {
                    'bits': 64
                },
                'egpr25': {
                    'bits': 64
                },
                'egpr26': {
                    'bits': 64
                },
                'egpr27': {
                    'bits': 64
                },
                'egpr28': {
                    'bits': 64
                },
                'egpr29': {
                    'bits': 64
                },
                'egpr30': {
                    'bits': 64
                },
                'egpr31': {
                    'bits': 64
                }
            }
        },
        'GU': {
            'base': [
                p2020_ccsrbar+0xE0000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'PORPLLSR': {
                    'access': 'r',
                    'offset': 0x0
                },
                'PORBMSR': {
                    'access': 'r',
                    'offset': 0x4
                },
                'PORDEVSR': {
                    'access': 'r',
                    'offset': 0xC
                },
                'PORDBGMSR': {
                    'access': 'r',
                    'offset': 0x10
                },
                'PORDEVSR2': {
                    'access': 'r',
                    'offset': 0x14
                },
                'GPPORCR': {
                    'access': 'r',
                    'offset': 0x20
                },
                'PMUXCR': {
                    'access': 'rw',
                    'offset': 0x60
                },
                'DEVDISR': {
                    'access': 'rw',
                    'offset': 0x70
                },
                'POWMGTCSR': {
                    'access': 'rw',
                    'offset': 0x80
                },
                'PMCDR': {
                    'access': 'rw',
                    'offset': 0x8C
                },
                'MCPSUMR': {
                    'access': 'w1c',
                    'offset': 0x90
                },
                'RSTRSCR': {
                    'access': 'rw',
                    'offset': 0x94
                },
                'ECTRSTCR': {
                    'access': 'rw',
                    'offset': 0x98
                },
                'AUTORSTSR': {
                    'access': 'w1c',
                    'offset': 0x9C
                },
                'PVR': {
                    'access': 'r',
                    'offset': 0xA0
                },
                'SVR': {
                    'access': 'r',
                    'offset': 0xA4
                },
                'RSTCR': {
                    'access': 'rw',
                    'offset': 0xB0
                },
                'IOVSELSR': {
                    'access': 'r',
                    'offset': 0xC0
                },
                'DDRCLKDR': {
                    'access': 'rw',
                    'offset': 0xB28
                },
                'CLKOCR': {
                    'access': 'rw',
                    'offset': 0xE00
                },
                'ECMCR': {
                    'access': 'rw',
                    'offset': 0xE20
                },
                'SDHCDCR': {
                    'access': 'rw',
                    'offset': 0xF64
                },
                'SRDSCR0': {
                    'access': 'rw',
                    'offset': 0x3000
                },
                'SRDSCR1': {
                    'access': 'rw',
                    'offset': 0x3004
                },
                'SRDSCR2': {
                    'access': 'rw',
                    'offset': 0x3008
                },
                'SRDSCR4': {
                    'access': 'rw',
                    'offset': 0x3010
                },
                'SRDSCR5': {
                    'access': 'rw',
                    'offset': 0x3014
                },
                'SRDSCR6': {
                    'access': 'rw',
                    'offset': 0x3018
                }
            }
        },
        'I2C': {
            'base': [
                p2020_ccsrbar+0x3000,
                p2020_ccsrbar+0x3100
            ],
            'count': 2,
            'memory_mapped': True,
            'registers': {
                'I2CADR': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x0
                },
                'I2CFDR': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x4
                },
                'I2CCR': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x8
                },
                'I2CSR': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0xC
                },
                'I2CDR': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x10
                },
                'I2CDFSRR': {
                    'access': 'rw',
                    'bits': 8,
                    'offset': 0x14
                }
            }
        },
        'L2SRAM': {
            'base': [
                p2020_ccsrbar+0x2000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'L2CTL': {
                    'access': 'rw',
                    'offset': 0x0
                },
                'L2CWAP': {
                    'access': 'rw',
                    'offset': 0x4
                },
                'L2CEWAR0': {
                    'access': 'rw',
                    'offset': 0x10
                },
                'L2CEWAREA0': {
                    'access': 'rw',
                    'offset': 0x14
                },
                'L2CEWCR0': {
                    'access': 'rw',
                    'offset': 0x18
                },
                'L2CEWAR1': {
                    'access': 'rw',
                    'offset': 0x20
                },
                'L2CEWAREA1': {
                    'access': 'rw',
                    'offset': 0x24
                },
                'L2CEWCR1': {
                    'access': 'rw',
                    'offset': 0x28
                },
                'L2CEWAR2': {
                    'access': 'rw',
                    'offset': 0x30
                },
                'L2CEWAREA2': {
                    'access': 'rw',
                    'offset': 0x34
                },
                'L2CEWCR2': {
                    'access': 'rw',
                    'offset': 0x38
                },
                'L2CEWAR3': {
                    'access': 'rw',
                    'offset': 0x40
                },
                'L2CEWAREA3': {
                    'access': 'rw',
                    'offset': 0x44
                },
                'L2CEWCR3': {
                    'access': 'rw',
                    'offset': 0x48
                },
                'L2SRBAR0': {
                    'access': 'rw',
                    'offset': 0x100
                },
                'L2SRBAREA0': {
                    'access': 'rw',
                    'offset': 0x104
                },
                'L2SRBAR1': {
                    'access': 'rw',
                    'offset': 0x108
                },
                'L2SRBAREA1': {
                    'access': 'rw',
                    'offset': 0x10C
                },
                'L2ERRINJHI': {
                    'access': 'rw',
                    'offset': 0xE00
                },
                'L2ERRINJLO': {
                    'access': 'rw',
                    'offset': 0xE04
                },
                'L2ERRINJCTL': {
                    'access': 'rw',
                    'offset': 0xE08
                },
                'L2CAPTDATAHI': {
                    'access': 'r',
                    'offset': 0xE20
                },
                'L2CAPTDATALO': {
                    'access': 'r',
                    'offset': 0xE24
                },
                'L2CAPTECC': {
                    'access': 'r',
                    'offset': 0xE28
                },
                'L2ERRDET': {
                    'access': 'w1c',
                    'offset': 0xE40
                },
                'L2ERRDIS': {
                    'access': 'rw',
                    'offset': 0xE44
                },
                'L2ERRINTEN': {
                    'access': 'rw',
                    'offset': 0xE48
                },
                'L2ERRATTR': {
                    'access': 'rw',
                    'offset': 0xE4C
                },
                'L2ERRADDRL': {
                    'access': 'r',
                    'offset': 0xE50
                },
                'L2ERRADDRH': {
                    'access': 'r',
                    'offset': 0xE54
                },
                'L2ERRCTL': {
                    'access': 'rw',
                    'offset': 0xE58
                }
            }
        },
        'LAW': {
            'base': [
                p2020_ccsrbar
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'LAWBAR0': {
                    'access': 'rw',
                    'offset': 0xC08
                },
                'LAWAR0': {
                    'access': 'rw',
                    'offset': 0xC10
                },
                'LAWBAR1': {
                    'access': 'rw',
                    'offset': 0xC28
                },
                'LAWAR1': {
                    'access': 'rw',
                    'offset': 0xC30
                },
                'LAWBAR2': {
                    'access': 'rw',
                    'offset': 0xC48
                },
                'LAWAR2': {
                    'access': 'rw',
                    'offset': 0xC50
                },
                'LAWBAR3': {
                    'access': 'rw',
                    'offset': 0xC68
                },
                'LAWAR3': {
                    'access': 'rw',
                    'offset': 0xC70
                },
                'LAWBAR4': {
                    'access': 'rw',
                    'offset': 0xC88
                },
                'LAWAR4': {
                    'access': 'rw',
                    'offset': 0xC90
                },
                'LAWBAR5': {
                    'access': 'rw',
                    'offset': 0xCA8
                },
                'LAWAR5': {
                    'access': 'rw',
                    'offset': 0xCB0
                },
                'LAWBAR6': {
                    'access': 'rw',
                    'offset': 0xCC8
                },
                'LAWAR6': {
                    'access': 'rw',
                    'offset': 0xCD0
                },
                'LAWBAR7': {
                    'access': 'rw',
                    'offset': 0xCE8
                },
                'LAWAR7': {
                    'access': 'rw',
                    'offset': 0xCF0
                },
                'LAWBAR8': {
                    'access': 'rw',
                    'offset': 0xD08
                },
                'LAWAR8': {
                    'access': 'rw',
                    'offset': 0xD10
                },
                'LAWBAR9': {
                    'access': 'rw',
                    'offset': 0xD28
                },
                'LAWAR9': {
                    'access': 'rw',
                    'offset': 0xD30
                },
                'LAWBAR10': {
                    'access': 'rw',
                    'offset': 0xD48
                },
                'LAWAR10': {
                    'access': 'rw',
                    'offset': 0xD50
                },
                'LAWBAR11': {
                    'access': 'rw',
                    'offset': 0xD68
                },
                'LAWAR11': {
                    'access': 'rw',
                    'offset': 0xD70
                }
            }
        },
        'MC': {
            'base': [
                p2020_ccsrbar+0x2000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'CS0_BNDS': {
                    'access': 'rw',
                    'offset': 0x0
                },
                'CS1_BNDS': {
                    'access': 'rw',
                    'offset': 0x8
                },
                'CS2_BNDS': {
                    'access': 'rw',
                    'offset': 0x10
                },
                'CS3_BNDS': {
                    'access': 'rw',
                    'offset': 0x18
                },
                'CS0_CONFIG': {
                    'access': 'rw',
                    'offset': 0x80
                },
                'CS1_CONFIG': {
                    'access': 'rw',
                    'offset': 0x84
                },
                'CS2_CONFIG': {
                    'access': 'rw',
                    'offset': 0x88
                },
                'CS3_CONFIG': {
                    'access': 'rw',
                    'offset': 0x8C
                },
                'CS0_CONFIG_2': {
                    'access': 'rw',
                    'offset': 0xC0
                },
                'CS1_CONFIG_2': {
                    'access': 'rw',
                    'offset': 0xC4
                },
                'CS2_CONFIG_2': {
                    'access': 'rw',
                    'offset': 0xC8
                },
                'CS3_CONFIG_2': {
                    'access': 'rw',
                    'offset': 0xCC
                },
                'TIMING_CFG_3': {
                    'access': 'rw',
                    'offset': 0x100
                },
                'TIMING_CFG_0': {
                    'access': 'rw',
                    'offset': 0x104
                },
                'TIMING_CFG_1': {
                    'access': 'rw',
                    'offset': 0x108
                },
                'TIMING_CFG_2': {
                    'access': 'rw',
                    'offset': 0x10C
                },
                'DDR_SDRAM_CFG': {
                    'access': 'rw',
                    'offset': 0x110
                },
                'DDR_SDRAM_CFG_2': {
                    'access': 'rw',
                    'offset': 0x114
                },
                'DDR_SDRAM_MODE': {
                    'access': 'rw',
                    'offset': 0x118
                },
                'DDR_SDRAM_MODE_2': {
                    'access': 'rw',
                    'offset': 0x11C
                },
                'DDR_SDRAM_MD_CNTL': {
                    'access': 'rw',
                    'offset': 0x120
                },
                'DDR_SDRAM_INTERVAL': {
                    'access': 'rw',
                    'offset': 0x124
                },
                'DDR_DATA_INIT': {
                    'access': 'rw',
                    'offset': 0x128
                },
                'DDR_SDRAM_CLK_CNTL': {
                    'access': 'rw',
                    'offset': 0x130
                },
                'DDR_INIT_ADDR': {
                    'access': 'rw',
                    'offset': 0x148
                },
                'DDR_INIT_EXT_ADDR': {
                    'access': 'rw',
                    'offset': 0x14C
                },
                'TIMING_CFG_4': {
                    'access': 'rw',
                    'offset': 0x160
                },
                'TIMING_CFG_5': {
                    'access': 'rw',
                    'offset': 0x164
                },
                'DDR_ZQ_CNTL': {
                    'access': 'rw',
                    'offset': 0x170
                },
                'DDR_WRLVL_CNTL': {
                    'access': 'rw',
                    'offset': 0x174
                },
                'DDR_SR_CNTR': {
                    'access': 'rw',
                    'offset': 0x17C
                },
                'DDR_SDRAM_RCW_1': {
                    'access': 'rw',
                    'offset': 0x180
                },
                'DDR_SDRAM_RCW_2': {
                    'access': 'rw',
                    'offset': 0x184
                },
                'DDR_WRLVL_CNTL_2': {
                    'access': 'rw',
                    'offset': 0x190
                },
                'DDR_WRLVL_CNTL_3': {
                    'access': 'rw',
                    'offset': 0x194
                },
                'DDRDSR_1': {
                    'access': 'r',
                    'offset': 0xB20
                },
                'DDRDSR_2': {
                    'access': 'r',
                    'offset': 0xB24
                },
                'DDRCDR_1': {
                    'access': 'rw',
                    'offset': 0xB28
                },
                'DDRCDR_2': {
                    'access': 'rw',
                    'offset': 0xB2C
                },
                'DDR_IP_REV1': {
                    'access': 'r',
                    'offset': 0xBF8
                },
                'DDR_IP_REV2': {
                    'access': 'r',
                    'offset': 0xBFC
                },
                'DATA_ERR_INJECT_HI': {
                    'access': 'rw',
                    'offset': 0xE00
                },
                'DATA_ERR_INJECT_LO': {
                    'access': 'rw',
                    'offset': 0xE04
                },
                'ERR_INJECT': {
                    'access': 'rw',
                    'offset': 0xE08
                },
                'CAPTURE_DATA_HI': {
                    'access': 'rw',
                    'offset': 0xE20
                },
                'CAPTURE_DATA_LO': {
                    'access': 'rw',
                    'offset': 0xE24
                },
                'CAPTURE_ECC': {
                    'access': 'rw',
                    'offset': 0xE28
                },
                'ERR_DETECT': {
                    'access': 'w1c',
                    'offset': 0xE40
                },
                'ERR_DISABLE': {
                    'access': 'rw',
                    'offset': 0xE44
                },
                'ERR_INT_EN': {
                    'access': 'rw',
                    'offset': 0xE48
                },
                'CAPTURE_ATTRIBUTES': {
                    'access': 'rw',
                    'offset': 0xE4C
                },
                'CAPTURE_ADDRESS': {
                    'access': 'rw',
                    'offset': 0xE50
                },
                'CAPTURE_EXT_ADDRESS': {
                    'access': 'rw',
                    'offset': 0xE54
                },
                'ERR_SBE': {
                    'access': 'rw',
                    'offset': 0xE58
                }
            }
        },
        'PCIE': {
            'base': [
                p2020_ccsrbar+0xA000,
                p2020_ccsrbar+0x9000,
                p2020_ccsrbar+0x8000
            ],
            'count': 3,
            'memory_mapped': True,
            'registers': {
                'PEX_CONFIG_ADDR': {
                    'access': 'rw',
                    'offset': 0x0
                },
                'PEX_CONFIG_DATA': {
                    'access': 'rw',
                    'offset': 0x4
                },
                'PEX_OTB_CPL_TOR': {
                    'access': 'rw',
                    'offset': 0xC
                },
                'PEX_CONF_RTY_TOR': {
                    'access': 'rw',
                    'offset': 0x10
                },
                'PEX_CONFIG': {
                    'access': 'rw',
                    'offset': 0x14
                },
                'PEX_PME_MES_DR': {
                    'access': 'w1c',
                    'offset': 0x20
                },
                'PEX_PME_MES_DISR': {
                    'access': 'rw',
                    'offset': 0x24
                },
                'PEX_PME_MES_IER': {
                    'access': 'rw',
                    'offset': 0x28
                },
                'PEX_PMCR': {
                    'access': 'rw',
                    'offset': 0x2C
                },
                'PEX_IP_BLK_REV1': {
                    'access': 'r',
                    'offset': 0xBF8
                },
                'PEX_IP_BLK_REV2': {
                    'access': 'r',
                    'offset': 0xBFC
                },
                'PEXOTAR0': {
                    'access': 'rw',
                    'offset': 0xC00
                },
                'PEXOTEAR0': {
                    'access': 'rw',
                    'offset': 0xC04
                },
                'PEXOWAR0': {
                    'access': 'rw',
                    'offset': 0xC10
                },
                'PEXOTAR1': {
                    'access': 'rw',
                    'offset': 0xC20
                },
                'PEXOTEAR1': {
                    'access': 'rw',
                    'offset': 0xC24
                },
                'PEXOWBAR1': {
                    'access': 'rw',
                    'offset': 0xC28
                },
                'PEXOWAR1': {
                    'access': 'rw',
                    'offset': 0xC30
                },
                'PEXOTAR2': {
                    'access': 'rw',
                    'offset': 0xC40
                },
                'PEXOTEAR2': {
                    'access': 'rw',
                    'offset': 0xC44
                },
                'PEXOWBAR2': {
                    'access': 'rw',
                    'offset': 0xC48
                },
                'PEXOWAR2': {
                    'access': 'rw',
                    'offset': 0xC50
                },
                'PEXOTAR3': {
                    'access': 'rw',
                    'offset': 0xC60
                },
                'PEXOTEAR3': {
                    'access': 'rw',
                    'offset': 0xC64
                },
                'PEXOWBAR3': {
                    'access': 'rw',
                    'offset': 0xC68
                },
                'PEXOWAR3': {
                    'access': 'rw',
                    'offset': 0xC70
                },
                'PEXOTAR4': {
                    'access': 'rw',
                    'offset': 0xC80
                },
                'PEXOTEAR4': {
                    'access': 'rw',
                    'offset': 0xC84
                },
                'PEXOWBAR4': {
                    'access': 'rw',
                    'offset': 0xC88
                },
                'PEXOWAR4': {
                    'access': 'rw',
                    'offset': 0xC90
                },
                'PEXITAR3': {
                    'access': 'rw',
                    'offset': 0xDA0
                },
                'PEXIWBAR3': {
                    'access': 'rw',
                    'offset': 0xDA8
                },
                'PEXIWBEAR3': {
                    'access': 'rw',
                    'offset': 0xDAC
                },
                'PEXIWAR3': {
                    'access': 'rw',
                    'offset': 0xDB0
                },
                'PEXITAR2': {
                    'access': 'rw',
                    'offset': 0xDC0
                },
                'PEXIWBAR2': {
                    'access': 'rw',
                    'offset': 0xDC8
                },
                'PEXIWBEAR2': {
                    'access': 'rw',
                    'offset': 0xDCC
                },
                'PEXIWAR2': {
                    'access': 'rw',
                    'offset': 0xDD0
                },
                'PEXITAR1': {
                    'access': 'rw',
                    'offset': 0xDE0
                },
                'PEXIWBAR1': {
                    'access': 'rw',
                    'offset': 0xDE8
                },
                'PEXIWAR1': {
                    'access': 'rw',
                    'offset': 0xDF0
                },
                'PEX_ERR_DR': {
                    'access': 'w1c',
                    'offset': 0xE00
                },
                'PEX_ERR_EN': {
                    'access': 'rw',
                    'offset': 0xE08
                },
                'PEX_ERR_DISR': {
                    'access': 'rw',
                    'offset': 0xE10
                },
                'PEX_ERR_CAP_STAT': {
                    'access': 'rw',
                    'offset': 0xE20
                },
                'PEX_ERR_CAP_R0': {
                    'access': 'rw',
                    'offset': 0xE28
                },
                'PEX_ERR_CAP_R1': {
                    'access': 'rw',
                    'offset': 0xE2C
                },
                'PEX_ERR_CAP_R2': {
                    'access': 'rw',
                    'offset': 0xE30
                },
                'PEX_ERR_CAP_R3': {
                    'access': 'rw',
                    'offset': 0xE34
                }
            }
        },
        'PERFMON': {
            'base': [
                p2020_ccsrbar+0xE1000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'PMGC0': {
                    'access': 'rw',
                    'offset': 0x0
                },
                'PMLCA0': {
                    'access': 'rw',
                    'offset': 0x10
                },
                'PMLCB0': {
                    'access': 'rw',
                    'offset': 0x14
                },
                'PMC0_lower': {
                    'access': 'rw',
                    'offset': 0x18
                },
                'PMC0_upper': {
                    'access': 'rw',
                    'offset': 0x1C
                },
                'PMLCA1': {
                    'access': 'rw',
                    'offset': 0x20
                },
                'PMLCB1': {
                    'access': 'rw',
                    'offset': 0x24
                },
                'PMC1': {
                    'access': 'rw',
                    'offset': 0x28
                },
                'PMLCA2': {
                    'access': 'rw',
                    'offset': 0x30
                },
                'PMLCB2': {
                    'access': 'rw',
                    'offset': 0x34
                },
                'PMC2': {
                    'access': 'rw',
                    'offset': 0x38
                },
                'PMLCA3': {
                    'access': 'rw',
                    'offset': 0x40
                },
                'PMLCB3': {
                    'access': 'rw',
                    'offset': 0x44
                },
                'PMC3': {
                    'access': 'rw',
                    'offset': 0x48
                },
                'PMLCA4': {
                    'access': 'rw',
                    'offset': 0x50
                },
                'PMLCB4': {
                    'access': 'rw',
                    'offset': 0x54
                },
                'PMC4': {
                    'access': 'rw',
                    'offset': 0x58
                },
                'PMLCA5': {
                    'access': 'rw',
                    'offset': 0x60
                },
                'PMLCB5': {
                    'access': 'rw',
                    'offset': 0x64
                },
                'PMC5': {
                    'access': 'rw',
                    'offset': 0x68
                },
                'PMLCA6': {
                    'access': 'rw',
                    'offset': 0x70
                },
                'PMLCB6': {
                    'access': 'rw',
                    'offset': 0x74
                },
                'PMC6': {
                    'access': 'rw',
                    'offset': 0x78
                },
                'PMLCA7': {
                    'access': 'rw',
                    'offset': 0x80
                },
                'PMLCB7': {
                    'access': 'rw',
                    'offset': 0x84
                },
                'PMC7': {
                    'access': 'rw',
                    'offset': 0x88
                },
                'PMLCA8': {
                    'access': 'rw',
                    'offset': 0x90
                },
                'PMLCB8': {
                    'access': 'rw',
                    'offset': 0x94
                },
                'PMC8': {
                    'access': 'rw',
                    'offset': 0x98
                },
                'PMLCA9': {
                    'access': 'rw',
                    'offset': 0xA0
                },
                'PMLCB9': {
                    'access': 'rw',
                    'offset': 0xA4
                },
                'PMC9': {
                    'access': 'rw',
                    'offset': 0xA8
                },
                'PMLCA10': {
                    'access': 'rw',
                    'offset': 0xB0
                },
                'PMLCB10': {
                    'access': 'rw',
                    'offset': 0xB4
                },
                'PMC10': {
                    'access': 'rw',
                    'offset': 0xB8
                },
                'PMLCA11': {
                    'access': 'rw',
                    'offset': 0xC0
                },
                'PMLCB11': {
                    'access': 'rw',
                    'offset': 0xC4
                },
                'PMC11': {
                    'access': 'rw',
                    'offset': 0xC8
                }
            }
        },
        'PIC': {
            'base': [
                p2020_ccsrbar+0x40000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'BRR1': {
                    'access': 'r',
                    'offset': 0x0
                },
                'BRR2': {
                    'access': 'r',
                    'offset': 0x10
                },
                'IPIDR0': {
                    'access': 'w',
                    'offset': 0x40
                },
                'IPIDR1': {
                    'access': 'w',
                    'offset': 0x50
                },
                'IPIDR2': {
                    'access': 'w',
                    'offset': 0x60
                },
                'IPIDR3': {
                    'access': 'w',
                    'offset': 0x70
                },
                'CTPR': {
                    'access': 'rw',
                    'offset': 0x80
                },
                'WHOAMI': {
                    'access': 'r',
                    'offset': 0x90
                },
                'IACK': {
                    'access': 'r',
                    'offset': 0xA0
                },
                'EOI': {
                    'access': 'w',
                    'offset': 0xB0
                },
                'FRR': {
                    'access': 'r',
                    'offset': 0x1000
                },
                'GCR': {
                    'access': 'rw',
                    'offset': 0x1020
                },
                'VIR': {
                    'access': 'r',
                    'offset': 0x1080
                },
                'PIR': {
                    'access': 'rw',
                    'offset': 0x1090
                },
                'IPIVPR0': {
                    'access': 'rw',
                    'offset': 0x10A0
                },
                'IPIVPR1': {
                    'access': 'rw',
                    'offset': 0x10B0
                },
                'IPIVPR2': {
                    'access': 'rw',
                    'offset': 0x10C0
                },
                'IPIVPR3': {
                    'access': 'rw',
                    'offset': 0x10D0
                },
                'SVR': {
                    'access': 'rw',
                    'offset': 0x10E0
                },
                'TFRRA': {
                    'access': 'rw',
                    'offset': 0x10F0
                },
                'GTCCRA0': {
                    'access': 'r',
                    'offset': 0x1100
                },
                'GTBCRA0': {
                    'access': 'rw',
                    'offset': 0x1110
                },
                'GTVPRA0': {
                    'access': 'rw',
                    'offset': 0x1120
                },
                'GTDRA0': {
                    'access': 'rw',
                    'offset': 0x1130
                },
                'GTCCRA1': {
                    'access': 'r',
                    'offset': 0x1140
                },
                'GTBCRA1': {
                    'access': 'rw',
                    'offset': 0x1150
                },
                'GTVPRA1': {
                    'access': 'rw',
                    'offset': 0x1160
                },
                'GTDRA1': {
                    'access': 'rw',
                    'offset': 0x1170
                },
                'GTCCRA2': {
                    'access': 'r',
                    'offset': 0x1180
                },
                'GTBCRA2': {
                    'access': 'rw',
                    'offset': 0x1190
                },
                'GTVPRA2': {
                    'access': 'rw',
                    'offset': 0x11A0
                },
                'GTDRA2': {
                    'access': 'rw',
                    'offset': 0x11B0
                },
                'GTCCRA3': {
                    'access': 'r',
                    'offset': 0x11C0
                },
                'GTBCRA3': {
                    'access': 'rw',
                    'offset': 0x11D0
                },
                'GTVPRA3': {
                    'access': 'rw',
                    'offset': 0x11E0
                },
                'GTDRA3': {
                    'access': 'rw',
                    'offset': 0x11F0
                },
                'TCRA': {
                    'access': 'rw',
                    'offset': 0x1300
                },
                'ERQSR': {
                    'access': 'r',
                    'offset': 0x1308
                },
                'IRQSR0': {
                    'access': 'r',
                    'offset': 0x1310
                },
                'IRQSR1': {
                    'access': 'r',
                    'offset': 0x1320
                },
                'IRQSR2': {
                    'access': 'r',
                    'offset': 0x1324
                },
                'CISR0': {
                    'access': 'r',
                    'offset': 0x1330
                },
                'CISR1': {
                    'access': 'r',
                    'offset': 0x1340
                },
                'CISR2': {
                    'access': 'r',
                    'offset': 0x1344
                },
                'PM0MR0': {
                    'access': 'rw',
                    'offset': 0x1350
                },
                'PM0MR1': {
                    'access': 'rw',
                    'offset': 0x1360
                },
                'PM0MR2': {
                    'access': 'rw',
                    'offset': 0x1364
                },
                'PM1MR0': {
                    'access': 'rw',
                    'offset': 0x1370
                },
                'PM1MR1': {
                    'access': 'rw',
                    'offset': 0x1380
                },
                'PM1MR2': {
                    'access': 'rw',
                    'offset': 0x1384
                },
                'PM2MR0': {
                    'access': 'rw',
                    'offset': 0x1390
                },
                'PM2MR1': {
                    'access': 'rw',
                    'offset': 0x13A0
                },
                'PM2MR2': {
                    'access': 'rw',
                    'offset': 0x13A4
                },
                'PM3MR0': {
                    'access': 'rw',
                    'offset': 0x13B0
                },
                'PM3MR1': {
                    'access': 'rw',
                    'offset': 0x13C0
                },
                'PM3MR2': {
                    'access': 'rw',
                    'offset': 0x13C4
                },
                'MSGR0': {
                    'access': 'rw',
                    'offset': 0x1400
                },
                'MSGR1': {
                    'access': 'rw',
                    'offset': 0x1410
                },
                'MSGR2': {
                    'access': 'rw',
                    'offset': 0x1420
                },
                'MSGR3': {
                    'access': 'rw',
                    'offset': 0x1430
                },
                'MER': {
                    'access': 'rw',
                    'offset': 0x1500
                },
                'MSR': {
                    'access': 'rw',
                    'offset': 0x1510
                },
                'MSIR0': {
                    'access': 'r',
                    'offset': 0x1600
                },
                'MSIR1': {
                    'access': 'r',
                    'offset': 0x1610
                },
                'MSIR2': {
                    'access': 'r',
                    'offset': 0x1620
                },
                'MSIR3': {
                    'access': 'r',
                    'offset': 0x1630
                },
                'MSIR4': {
                    'access': 'r',
                    'offset': 0x1640
                },
                'MSIR5': {
                    'access': 'r',
                    'offset': 0x1650
                },
                'MSIR6': {
                    'access': 'r',
                    'offset': 0x1660
                },
                'MSIR7': {
                    'access': 'r',
                    'offset': 0x1670
                },
                'MSISR': {
                    'access': 'r',
                    'offset': 0x1720
                },
                'MSIIR': {
                    'access': 'w',
                    'offset': 0x1740
                },
                'TFRRB': {
                    'access': 'rw',
                    'offset': 0x20F0
                },
                'GTCCRB0': {
                    'access': 'r',
                    'offset': 0x2100
                },
                'GTBCRB0': {
                    'access': 'rw',
                    'offset': 0x2110
                },
                'GTVPRB0': {
                    'access': 'rw',
                    'offset': 0x2120
                },
                'GTDRB0': {
                    'access': 'rw',
                    'offset': 0x2130
                },
                'GTCCRB1': {
                    'access': 'r',
                    'offset': 0x2140
                },
                'GTBCRB1': {
                    'access': 'rw',
                    'offset': 0x2150
                },
                'GTVPRB1': {
                    'access': 'rw',
                    'offset': 0x2160
                },
                'GTDRB1': {
                    'access': 'rw',
                    'offset': 0x2170
                },
                'GTCCRB2': {
                    'access': 'r',
                    'offset': 0x2180
                },
                'GTBCRB2': {
                    'access': 'rw',
                    'offset': 0x2190
                },
                'GTVPRB2': {
                    'access': 'rw',
                    'offset': 0x21A0
                },
                'GTDRB2': {
                    'access': 'rw',
                    'offset': 0x21B0
                },
                'GTCCRB3': {
                    'access': 'r',
                    'offset': 0x21C0
                },
                'GTBCRB3': {
                    'access': 'rw',
                    'offset': 0x21D0
                },
                'GTVPRB3': {
                    'access': 'rw',
                    'offset': 0x21E0
                },
                'GTDRB3': {
                    'access': 'rw',
                    'offset': 0x21F0
                },
                'TCRB': {
                    'access': 'rw',
                    'offset': 0x2300
                },
                'MSGRa4': {
                    'access': 'rw',
                    'offset': 0x2400
                },
                'MSGRa5': {
                    'access': 'rw',
                    'offset': 0x2410
                },
                'MSGRa6': {
                    'access': 'rw',
                    'offset': 0x2420
                },
                'MSGRa7': {
                    'access': 'rw',
                    'offset': 0x2430
                },
                'MERa': {
                    'access': 'rw',
                    'offset': 0x2500
                },
                'MSRa': {
                    'access': 'rw',
                    'offset': 0x2510
                },
                'EIVPR0': {
                    'access': 'rw',
                    'offset': 0x10000
                },
                'EIDR0': {
                    'access': 'rw',
                    'offset': 0x10010
                },
                'EIVPR1': {
                    'access': 'rw',
                    'offset': 0x10020
                },
                'EIDR1': {
                    'access': 'rw',
                    'offset': 0x10030
                },
                'EIVPR2': {
                    'access': 'rw',
                    'offset': 0x10040
                },
                'EIDR2': {
                    'access': 'rw',
                    'offset': 0x10050
                },
                'EIVPR3': {
                    'access': 'rw',
                    'offset': 0x10060
                },
                'EIDR3': {
                    'access': 'rw',
                    'offset': 0x10070
                },
                'EIVPR4': {
                    'access': 'rw',
                    'offset': 0x10080
                },
                'EIDR4': {
                    'access': 'rw',
                    'offset': 0x10090
                },
                'EIVPR5': {
                    'access': 'rw',
                    'offset': 0x100A0
                },
                'EIDR5': {
                    'access': 'rw',
                    'offset': 0x100B0
                },
                'EIVPR6': {
                    'access': 'rw',
                    'offset': 0x100C0
                },
                'EIDR6': {
                    'access': 'rw',
                    'offset': 0x100D0
                },
                'EIVPR7': {
                    'access': 'rw',
                    'offset': 0x100E0
                },
                'EIDR7': {
                    'access': 'rw',
                    'offset': 0x100F0
                },
                'EIVPR8': {
                    'access': 'rw',
                    'offset': 0x10100
                },
                'EIDR8': {
                    'access': 'rw',
                    'offset': 0x10110
                },
                'EIVPR9': {
                    'access': 'rw',
                    'offset': 0x10120
                },
                'EIDR9': {
                    'access': 'rw',
                    'offset': 0x10130
                },
                'EIVPR10': {
                    'access': 'rw',
                    'offset': 0x10140
                },
                'EIDR10': {
                    'access': 'rw',
                    'offset': 0x10150
                },
                'EIVPR11': {
                    'access': 'rw',
                    'offset': 0x10160
                },
                'EIDR11': {
                    'access': 'rw',
                    'offset': 0x10170
                },
                'IIVPR0': {
                    'access': 'rw',
                    'offset': 0x10200
                },
                'IIDR0': {
                    'access': 'rw',
                    'offset': 0x10210
                },
                'IIVPR1': {
                    'access': 'rw',
                    'offset': 0x10220
                },
                'IIDR1': {
                    'access': 'rw',
                    'offset': 0x10230
                },
                'IIVPR2': {
                    'access': 'rw',
                    'offset': 0x10240
                },
                'IIDR2': {
                    'access': 'rw',
                    'offset': 0x10250
                },
                'IIVPR3': {
                    'access': 'rw',
                    'offset': 0x10260
                },
                'IIDR3': {
                    'access': 'rw',
                    'offset': 0x10270
                },
                'IIVPR4': {
                    'access': 'rw',
                    'offset': 0x10280
                },
                'IIDR4': {
                    'access': 'rw',
                    'offset': 0x10290
                },
                'IIVPR5': {
                    'access': 'rw',
                    'offset': 0x102A0
                },
                'IIDR5': {
                    'access': 'rw',
                    'offset': 0x102B0
                },
                'IIVPR6': {
                    'access': 'rw',
                    'offset': 0x102C0
                },
                'IIDR6': {
                    'access': 'rw',
                    'offset': 0x102D0
                },
                'IIVPR7': {
                    'access': 'rw',
                    'offset': 0x102E0
                },
                'IIDR7': {
                    'access': 'rw',
                    'offset': 0x102F0
                },
                'IIVPR8': {
                    'access': 'rw',
                    'offset': 0x10300
                },
                'IIDR8': {
                    'access': 'rw',
                    'offset': 0x10310
                },
                'IIVPR9': {
                    'access': 'rw',
                    'offset': 0x10320
                },
                'IIDR9': {
                    'access': 'rw',
                    'offset': 0x10330
                },
                'IIVPR10': {
                    'access': 'rw',
                    'offset': 0x10340
                },
                'IIDR10': {
                    'access': 'rw',
                    'offset': 0x10350
                },
                'IIVPR11': {
                    'access': 'rw',
                    'offset': 0x10360
                },
                'IIDR11': {
                    'access': 'rw',
                    'offset': 0x10370
                },
                'IIVPR12': {
                    'access': 'rw',
                    'offset': 0x10380
                },
                'IIDR12': {
                    'access': 'rw',
                    'offset': 0x10390
                },
                'IIVPR13': {
                    'access': 'rw',
                    'offset': 0x103A0
                },
                'IIDR13': {
                    'access': 'rw',
                    'offset': 0x103B0
                },
                'IIVPR14': {
                    'access': 'rw',
                    'offset': 0x103C0
                },
                'IIDR14': {
                    'access': 'rw',
                    'offset': 0x103D0
                },
                'IIVPR15': {
                    'access': 'rw',
                    'offset': 0x103E0
                },
                'IIDR15': {
                    'access': 'rw',
                    'offset': 0x103F0
                },
                'IIVPR16': {
                    'access': 'rw',
                    'offset': 0x10400
                },
                'IIDR16': {
                    'access': 'rw',
                    'offset': 0x10410
                },
                'IIVPR17': {
                    'access': 'rw',
                    'offset': 0x10420
                },
                'IIDR17': {
                    'access': 'rw',
                    'offset': 0x10430
                },
                'IIVPR18': {
                    'access': 'rw',
                    'offset': 0x10440
                },
                'IIDR18': {
                    'access': 'rw',
                    'offset': 0x10450
                },
                'IIVPR19': {
                    'access': 'rw',
                    'offset': 0x10460
                },
                'IIDR19': {
                    'access': 'rw',
                    'offset': 0x10470
                },
                'IIVPR20': {
                    'access': 'rw',
                    'offset': 0x10480
                },
                'IIDR20': {
                    'access': 'rw',
                    'offset': 0x10490
                },
                'IIVPR21': {
                    'access': 'rw',
                    'offset': 0x104A0
                },
                'IIDR21': {
                    'access': 'rw',
                    'offset': 0x104B0
                },
                'IIVPR22': {
                    'access': 'rw',
                    'offset': 0x104C0
                },
                'IIDR22': {
                    'access': 'rw',
                    'offset': 0x104D0
                },
                'IIVPR23': {
                    'access': 'rw',
                    'offset': 0x104E0
                },
                'IIDR23': {
                    'access': 'rw',
                    'offset': 0x104F0
                },
                'IIVPR24': {
                    'access': 'rw',
                    'offset': 0x10500
                },
                'IIDR24': {
                    'access': 'rw',
                    'offset': 0x10510
                },
                'IIVPR25': {
                    'access': 'rw',
                    'offset': 0x10520
                },
                'IIDR25': {
                    'access': 'rw',
                    'offset': 0x10530
                },
                'IIVPR26': {
                    'access': 'rw',
                    'offset': 0x10540
                },
                'IIDR26': {
                    'access': 'rw',
                    'offset': 0x10550
                },
                'IIVPR27': {
                    'access': 'rw',
                    'offset': 0x10560
                },
                'IIDR27': {
                    'access': 'rw',
                    'offset': 0x10570
                },
                'IIVPR28': {
                    'access': 'rw',
                    'offset': 0x10580
                },
                'IIDR28': {
                    'access': 'rw',
                    'offset': 0x10590
                },
                'IIVPR29': {
                    'access': 'rw',
                    'offset': 0x105A0
                },
                'IIDR29': {
                    'access': 'rw',
                    'offset': 0x105B0
                },
                'IIVPR30': {
                    'access': 'rw',
                    'offset': 0x105C0
                },
                'IIDR30': {
                    'access': 'rw',
                    'offset': 0x105D0
                },
                'IIVPR31': {
                    'access': 'rw',
                    'offset': 0x105E0
                },
                'IIDR31': {
                    'access': 'rw',
                    'offset': 0x105F0
                },
                'IIVPR32': {
                    'access': 'rw',
                    'offset': 0x10600
                },
                'IIDR32': {
                    'access': 'rw',
                    'offset': 0x10610
                },
                'IIVPR33': {
                    'access': 'rw',
                    'offset': 0x10620
                },
                'IIDR33': {
                    'access': 'rw',
                    'offset': 0x10630
                },
                'IIVPR34': {
                    'access': 'rw',
                    'offset': 0x10640
                },
                'IIDR34': {
                    'access': 'rw',
                    'offset': 0x10650
                },
                'IIVPR35': {
                    'access': 'rw',
                    'offset': 0x10660
                },
                'IIDR35': {
                    'access': 'rw',
                    'offset': 0x10670
                },
                'IIVPR36': {
                    'access': 'rw',
                    'offset': 0x10680
                },
                'IIDR36': {
                    'access': 'rw',
                    'offset': 0x10690
                },
                'IIVPR37': {
                    'access': 'rw',
                    'offset': 0x106A0
                },
                'IIDR37': {
                    'access': 'rw',
                    'offset': 0x106B0
                },
                'IIVPR38': {
                    'access': 'rw',
                    'offset': 0x106C0
                },
                'IIDR38': {
                    'access': 'rw',
                    'offset': 0x106D0
                },
                'IIVPR39': {
                    'access': 'rw',
                    'offset': 0x106E0
                },
                'IIDR39': {
                    'access': 'rw',
                    'offset': 0x106F0
                },
                'IIVPR40': {
                    'access': 'rw',
                    'offset': 0x10700
                },
                'IIDR40': {
                    'access': 'rw',
                    'offset': 0x10710
                },
                'IIVPR41': {
                    'access': 'rw',
                    'offset': 0x10720
                },
                'IIDR41': {
                    'access': 'rw',
                    'offset': 0x10730
                },
                'IIVPR42': {
                    'access': 'rw',
                    'offset': 0x10740
                },
                'IIDR42': {
                    'access': 'rw',
                    'offset': 0x10750
                },
                'IIVPR43': {
                    'access': 'rw',
                    'offset': 0x10760
                },
                'IIDR43': {
                    'access': 'rw',
                    'offset': 0x10770
                },
                'IIVPR44': {
                    'access': 'rw',
                    'offset': 0x10780
                },
                'IIDR44': {
                    'access': 'rw',
                    'offset': 0x10790
                },
                'IIVPR45': {
                    'access': 'rw',
                    'offset': 0x107A0
                },
                'IIDR45': {
                    'access': 'rw',
                    'offset': 0x107B0
                },
                'IIVPR46': {
                    'access': 'rw',
                    'offset': 0x107C0
                },
                'IIDR46': {
                    'access': 'rw',
                    'offset': 0x107D0
                },
                'IIVPR47': {
                    'access': 'rw',
                    'offset': 0x107E0
                },
                'IIDR47': {
                    'access': 'rw',
                    'offset': 0x107F0
                },
                'IIVPR48': {
                    'access': 'rw',
                    'offset': 0x10800
                },
                'IIDR48': {
                    'access': 'rw',
                    'offset': 0x10810
                },
                'IIVPR49': {
                    'access': 'rw',
                    'offset': 0x10820
                },
                'IIDR49': {
                    'access': 'rw',
                    'offset': 0x10830
                },
                'IIVPR50': {
                    'access': 'rw',
                    'offset': 0x10840
                },
                'IIDR50': {
                    'access': 'rw',
                    'offset': 0x10850
                },
                'IIVPR51': {
                    'access': 'rw',
                    'offset': 0x10860
                },
                'IIDR51': {
                    'access': 'rw',
                    'offset': 0x10870
                },
                'IIVPR52': {
                    'access': 'rw',
                    'offset': 0x10880
                },
                'IIDR52': {
                    'access': 'rw',
                    'offset': 0x10890
                },
                'IIVPR53': {
                    'access': 'rw',
                    'offset': 0x108A0
                },
                'IIDR53': {
                    'access': 'rw',
                    'offset': 0x108B0
                },
                'IIVPR54': {
                    'access': 'rw',
                    'offset': 0x108C0
                },
                'IIDR54': {
                    'access': 'rw',
                    'offset': 0x108D0
                },
                'IIVPR55': {
                    'access': 'rw',
                    'offset': 0x108E0
                },
                'IIDR55': {
                    'access': 'rw',
                    'offset': 0x108F0
                },
                'IIVPR56': {
                    'access': 'rw',
                    'offset': 0x10900
                },
                'IIDR56': {
                    'access': 'rw',
                    'offset': 0x10910
                },
                'IIVPR57': {
                    'access': 'rw',
                    'offset': 0x10920
                },
                'IIDR57': {
                    'access': 'rw',
                    'offset': 0x10930
                },
                'IIVPR58': {
                    'access': 'rw',
                    'offset': 0x10940
                },
                'IIDR58': {
                    'access': 'rw',
                    'offset': 0x10950
                },
                'IIVPR59': {
                    'access': 'rw',
                    'offset': 0x10960
                },
                'IIDR59': {
                    'access': 'rw',
                    'offset': 0x10970
                },
                'IIVPR60': {
                    'access': 'rw',
                    'offset': 0x10980
                },
                'IIDR60': {
                    'access': 'rw',
                    'offset': 0x10990
                },
                'IIVPR61': {
                    'access': 'rw',
                    'offset': 0x109A0
                },
                'IIDR61': {
                    'access': 'rw',
                    'offset': 0x109B0
                },
                'IIVPR62': {
                    'access': 'rw',
                    'offset': 0x109C0
                },
                'IIDR62': {
                    'access': 'rw',
                    'offset': 0x109D0
                },
                'IIVPR63': {
                    'access': 'rw',
                    'offset': 0x109E0
                },
                'IIDR63': {
                    'access': 'rw',
                    'offset': 0x109F0
                },
                'MIVPR0': {
                    'access': 'rw',
                    'offset': 0x11600
                },
                'MIDR0': {
                    'access': 'rw',
                    'offset': 0x11610
                },
                'MIVPR1': {
                    'access': 'rw',
                    'offset': 0x11620
                },
                'MIDR1': {
                    'access': 'rw',
                    'offset': 0x11630
                },
                'MIVPR2': {
                    'access': 'rw',
                    'offset': 0x11640
                },
                'MIDR2': {
                    'access': 'rw',
                    'offset': 0x11650
                },
                'MIVPR3': {
                    'access': 'rw',
                    'offset': 0x11660
                },
                'MIDR3': {
                    'access': 'rw',
                    'offset': 0x11670
                },
                'MIVPR4': {
                    'access': 'rw',
                    'offset': 0x11680
                },
                'MIDR4': {
                    'access': 'rw',
                    'offset': 0x11690
                },
                'MIVPR5': {
                    'access': 'rw',
                    'offset': 0x116A0
                },
                'MIDR5': {
                    'access': 'rw',
                    'offset': 0x116B0
                },
                'MIVPR6': {
                    'access': 'rw',
                    'offset': 0x116C0
                },
                'MIDR6': {
                    'access': 'rw',
                    'offset': 0x116D0
                },
                'MIVPR7': {
                    'access': 'rw',
                    'offset': 0x116E0
                },
                'MIDR7': {
                    'access': 'rw',
                    'offset': 0x116F0
                },
                'MSIVPR0': {
                    'access': 'rw',
                    'offset': 0x11C00
                },
                'MSIDR0': {
                    'access': 'rw',
                    'offset': 0x11C10
                },
                'MSIVPR1': {
                    'access': 'rw',
                    'offset': 0x11C20
                },
                'MSIDR1': {
                    'access': 'rw',
                    'offset': 0x11C30
                },
                'MSIVPR2': {
                    'access': 'rw',
                    'offset': 0x11C40
                },
                'MSIDR2': {
                    'access': 'rw',
                    'offset': 0x11C50
                },
                'MSIVPR3': {
                    'access': 'rw',
                    'offset': 0x11C60
                },
                'MSIDR3': {
                    'access': 'rw',
                    'offset': 0x11C70
                },
                'MSIVPR4': {
                    'access': 'rw',
                    'offset': 0x11C80
                },
                'MSIDR4': {
                    'access': 'rw',
                    'offset': 0x11C90
                },
                'MSIVPR5': {
                    'access': 'rw',
                    'offset': 0x11CA0
                },
                'MSIDR5': {
                    'access': 'rw',
                    'offset': 0x11CB0
                },
                'MSIVPR6': {
                    'access': 'rw',
                    'offset': 0x11CC0
                },
                'MSIDR6': {
                    'access': 'rw',
                    'offset': 0x11CD0
                },
                'MSIVPR7': {
                    'access': 'rw',
                    'offset': 0x11CE0
                },
                'MSIDR7': {
                    'access': 'rw',
                    'offset': 0x11CF0
                },
                'IPIDR_CPU00': {
                    'access': 'w',
                    'offset': 0x20040
                },
                'IPIDR_CPU01': {
                    'access': 'w',
                    'offset': 0x20050
                },
                'IPIDR_CPU02': {
                    'access': 'w',
                    'offset': 0x20060
                },
                'IPIDR_CPU03': {
                    'access': 'w',
                    'offset': 0x20070
                },
                'CTPR_CPU0': {
                    'access': 'rw',
                    'offset': 0x20080
                },
                'WHOAMI_CPU0': {
                    'access': 'r',
                    'offset': 0x20090
                },
                'IACK_CPU0': {
                    'access': 'r',
                    'offset': 0x200A0
                },
                'EOI_CPU0': {
                    'access': 'w',
                    'offset': 0x200B0
                },
                'IPIDR_CPU10': {
                    'access': 'w',
                    'offset': 0x21040
                },
                'IPIDR_CPU11': {
                    'access': 'w',
                    'offset': 0x21050
                },
                'IPIDR_CPU12': {
                    'access': 'w',
                    'offset': 0x21060
                },
                'IPIDR_CPU13': {
                    'access': 'w',
                    'offset': 0x21070
                },
                'CTPR_CPU1': {
                    'access': 'rw',
                    'offset': 0x21080
                },
                'WHOAMI_CPU1': {
                    'access': 'r',
                    'offset': 0x21090
                },
                'IACK_CPU1': {
                    'access': 'r',
                    'offset': 0x210A0
                },
                'EOI_CPU1': {
                    'access': 'w',
                    'offset': 0x210B0
                }
            }
        },
        'RAPIDIO': {
            'base': [
                p2020_ccsrbar+0xC0000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'DIDCAR': {
                    'access': 'r',
                    'offset': 0x0
                },
                'DICAR': {
                    'access': 'r',
                    'offset': 0x4
                },
                'AIDCAR': {
                    'access': 'rw',
                    'offset': 0x8
                },
                'AICAR': {
                    'access': 'rw',
                    'offset': 0xC
                },
                'PEFCAR': {
                    'access': 'r',
                    'offset': 0x10
                },
                'SOCAR': {
                    'access': 'r',
                    'offset': 0x18
                },
                'DOCAR': {
                    'access': 'r',
                    'offset': 0x1C
                },
                'MCSR': {
                    'access': 'r',
                    'offset': 0x40
                },
                'PWDCSR': {
                    'access': 'r',
                    'offset': 0x44
                },
                'PELLCCSR': {
                    'access': 'r',
                    'offset': 0x4C
                },
                'LCSBA1CSR': {
                    'access': 'rw',
                    'offset': 0x5C
                },
                'BDIDCSR': {
                    'access': 'rw',
                    'offset': 0x60
                },
                'HBDIDLCSR': {
                    'access': 'rw',
                    'offset': 0x68
                },
                'CTCSR': {
                    'access': 'rw',
                    'offset': 0x6C
                },
                'PMBH0': {
                    'access': 'r',
                    'offset': 0x100
                },
                'PLTOCCSR': {
                    'access': 'rw',
                    'offset': 0x120
                },
                'PRTOCCSR': {
                    'access': 'rw',
                    'offset': 0x124
                },
                'PGCCSR': {
                    'access': 'rw',
                    'offset': 0x13C
                },
                'P1LMREQCSR': {
                    'access': 'rw',
                    'offset': 0x140
                },
                'P1LMRESPCSR': {
                    'access': 'r',
                    'offset': 0x144
                },
                'P1LASCSR': {
                    'access': 'rw',
                    'offset': 0x148
                },
                'P1ESCSR': {
                    'access': 'rw',
                    'offset': 0x158
                },
                'P1CCSR': {
                    'access': 'rw',
                    'offset': 0x15C
                },
                'P2LMREQCSR': {
                    'access': 'rw',
                    'offset': 0x160
                },
                'P2LMRESPCSR': {
                    'access': 'r',
                    'offset': 0x164
                },
                'P2LASCSR': {
                    'access': 'rw',
                    'offset': 0x168
                },
                'P2ESCSR': {
                    'access': 'rw',
                    'offset': 0x178
                },
                'P2CCSR': {
                    'access': 'rw',
                    'offset': 0x17C
                },
                'ERBH': {
                    'access': 'r',
                    'offset': 0x600
                },
                'LTLEDCSR': {
                    'access': 'rw',
                    'offset': 0x608
                },
                'LTLEECSR': {
                    'access': 'rw',
                    'offset': 0x60C
                },
                'LTLACCSR': {
                    'access': 'rw',
                    'offset': 0x614
                },
                'LTLDIDCCSR': {
                    'access': 'rw',
                    'offset': 0x618
                },
                'LTLCCCSR': {
                    'access': 'rw',
                    'offset': 0x61C
                },
                'P1EDCSR': {
                    'access': 'rw',
                    'offset': 0x640
                },
                'P1ERECSR': {
                    'access': 'rw',
                    'offset': 0x644
                },
                'P1ECACSR': {
                    'access': 'rw',
                    'offset': 0x648
                },
                'P1PCSECCSR0': {
                    'access': 'rw',
                    'offset': 0x64C
                },
                'P1PECCSR1': {
                    'access': 'rw',
                    'offset': 0x650
                },
                'P1PECCSR2': {
                    'access': 'rw',
                    'offset': 0x654
                },
                'P1PECCSR3': {
                    'access': 'rw',
                    'offset': 0x658
                },
                'P1ERCSR': {
                    'access': 'rw',
                    'offset': 0x668
                },
                'P1ERTCSR': {
                    'access': 'rw',
                    'offset': 0x66C
                },
                'P2EDCSR': {
                    'access': 'rw',
                    'offset': 0x680
                },
                'P2ERECSR': {
                    'access': 'rw',
                    'offset': 0x684
                },
                'P2ECACSR': {
                    'access': 'rw',
                    'offset': 0x688
                },
                'P2PCSECCSR0': {
                    'access': 'rw',
                    'offset': 0x68C
                },
                'P2PECCSR1': {
                    'access': 'rw',
                    'offset': 0x690
                },
                'P2PECCSR2': {
                    'access': 'rw',
                    'offset': 0x694
                },
                'P2PECCSR3': {
                    'access': 'rw',
                    'offset': 0x698
                },
                'P2ERCSR': {
                    'access': 'rw',
                    'offset': 0x6A8
                },
                'P2ERTCSR': {
                    'access': 'rw',
                    'offset': 0x6AC
                },
                'LLCR': {
                    'access': 'rw',
                    'offset': 0x10004
                },
                'EPWISR': {
                    'access': 'r',
                    'offset': 0x10010
                },
                'LRETCR': {
                    'access': 'rw',
                    'offset': 0x10020
                },
                'PRETCR': {
                    'access': 'rw',
                    'offset': 0x10080
                },
                'P1ADIDCSR': {
                    'access': 'rw',
                    'offset': 0x10100
                },
                'P1AACR': {
                    'access': 'rw',
                    'offset': 0x10120
                },
                'P1LOPTTLCR': {
                    'access': 'rw',
                    'offset': 0x10124
                },
                'P1IECSR': {
                    'access': 'w1c',
                    'offset': 0x10130
                },
                'P1PCR': {
                    'access': 'rw',
                    'offset': 0x10140
                },
                'P1SLCSR': {
                    'access': 'w1c',
                    'offset': 0x10158
                },
                'P1SLEICR': {
                    'access': 'rw',
                    'offset': 0x10160
                },
                'P2ADIDCSR': {
                    'access': 'rw',
                    'offset': 0x10180
                },
                'P2AACR': {
                    'access': 'rw',
                    'offset': 0x101A0
                },
                'P2LOPTTLCR': {
                    'access': 'rw',
                    'offset': 0x101A4
                },
                'P2IECSR': {
                    'access': 'w1c',
                    'offset': 0x101B0
                },
                'P2PCR': {
                    'access': 'rw',
                    'offset': 0x101C0
                },
                'P2SLCSR': {
                    'access': 'w1c',
                    'offset': 0x101D8
                },
                'P2SLEICR': {
                    'access': 'rw',
                    'offset': 0x101E0
                },
                'IPBRR1': {
                    'access': 'r',
                    'offset': 0x10BF8
                },
                'IPBRR2': {
                    'access': 'r',
                    'offset': 0x10BFC
                },
                'P1ROWTAR0': {
                    'access': 'rw',
                    'offset': 0x10C00
                },
                'P1ROWTEAR0': {
                    'access': 'rw',
                    'offset': 0x10C04
                },
                'P1ROWAR0': {
                    'access': 'rw',
                    'offset': 0x10C10
                },
                'P1ROWTAR1': {
                    'access': 'rw',
                    'offset': 0x10C20
                },
                'P1ROWTEAR1': {
                    'access': 'rw',
                    'offset': 0x10C24
                },
                'P1ROWBAR1': {
                    'access': 'rw',
                    'offset': 0x10C28
                },
                'P1ROWAR1': {
                    'access': 'rw',
                    'offset': 0x10C30
                },
                'P1ROWS1R1': {
                    'access': 'rw',
                    'offset': 0x10C34
                },
                'P1ROWS2R1': {
                    'access': 'rw',
                    'offset': 0x10C38
                },
                'P1ROWS3R1': {
                    'access': 'rw',
                    'offset': 0x10C3C
                },
                'P1ROWTAR2': {
                    'access': 'rw',
                    'offset': 0x10C40
                },
                'P1ROWTEAR2': {
                    'access': 'rw',
                    'offset': 0x10C44
                },
                'P1ROWBAR2': {
                    'access': 'rw',
                    'offset': 0x10C48
                },
                'P1ROWAR2': {
                    'access': 'rw',
                    'offset': 0x10C50
                },
                'P1ROWS1R2': {
                    'access': 'rw',
                    'offset': 0x10C54
                },
                'P1ROWS2R2': {
                    'access': 'rw',
                    'offset': 0x10C58
                },
                'P1ROWS3R2': {
                    'access': 'rw',
                    'offset': 0x10C5C
                },
                'P1ROWTAR3': {
                    'access': 'rw',
                    'offset': 0x10C60
                },
                'P1ROWTEAR3': {
                    'access': 'rw',
                    'offset': 0x10C64
                },
                'P1ROWBAR3': {
                    'access': 'rw',
                    'offset': 0x10C68
                },
                'P1ROWAR3': {
                    'access': 'rw',
                    'offset': 0x10C70
                },
                'P1ROWS1R3': {
                    'access': 'rw',
                    'offset': 0x10C74
                },
                'P1ROWS2R3': {
                    'access': 'rw',
                    'offset': 0x10C78
                },
                'P1ROWS3R3': {
                    'access': 'rw',
                    'offset': 0x10C7C
                },
                'P1ROWTAR4': {
                    'access': 'rw',
                    'offset': 0x10C80
                },
                'P1ROWTEAR4': {
                    'access': 'rw',
                    'offset': 0x10C84
                },
                'P1ROWBAR4': {
                    'access': 'rw',
                    'offset': 0x10C88
                },
                'P1ROWAR4': {
                    'access': 'rw',
                    'offset': 0x10C90
                },
                'P1ROWS1R4': {
                    'access': 'rw',
                    'offset': 0x10C94
                },
                'P1ROWS2R4': {
                    'access': 'rw',
                    'offset': 0x10C98
                },
                'P1ROWS3R4': {
                    'access': 'rw',
                    'offset': 0x10C9C
                },
                'P1ROWTAR5': {
                    'access': 'rw',
                    'offset': 0x10CA0
                },
                'P1ROWTEAR5': {
                    'access': 'rw',
                    'offset': 0x10CA4
                },
                'P1ROWBAR5': {
                    'access': 'rw',
                    'offset': 0x10CA8
                },
                'P1ROWAR5': {
                    'access': 'rw',
                    'offset': 0x10CB0
                },
                'P1ROWS1R5': {
                    'access': 'rw',
                    'offset': 0x10CB4
                },
                'P1ROWS2R5': {
                    'access': 'rw',
                    'offset': 0x10CB8
                },
                'P1ROWS3R5': {
                    'access': 'rw',
                    'offset': 0x10CBC
                },
                'P1ROWTAR6': {
                    'access': 'rw',
                    'offset': 0x10CC0
                },
                'P1ROWTEAR6': {
                    'access': 'rw',
                    'offset': 0x10CC4
                },
                'P1ROWBAR6': {
                    'access': 'rw',
                    'offset': 0x10CC8
                },
                'P1ROWAR6': {
                    'access': 'rw',
                    'offset': 0x10CD0
                },
                'P1ROWS1R6': {
                    'access': 'rw',
                    'offset': 0x10CD4
                },
                'P1ROWS2R6': {
                    'access': 'rw',
                    'offset': 0x10CD8
                },
                'P1ROWS3R6': {
                    'access': 'rw',
                    'offset': 0x10CDC
                },
                'P1ROWTAR7': {
                    'access': 'rw',
                    'offset': 0x10CE0
                },
                'P1ROWTEAR7': {
                    'access': 'rw',
                    'offset': 0x10CE4
                },
                'P1ROWBAR7': {
                    'access': 'rw',
                    'offset': 0x10CE8
                },
                'P1ROWAR7': {
                    'access': 'rw',
                    'offset': 0x10CF0
                },
                'P1ROWS1R7': {
                    'access': 'rw',
                    'offset': 0x10CF4
                },
                'P1ROWS2R7': {
                    'access': 'rw',
                    'offset': 0x10CF8
                },
                'P1ROWS3R7': {
                    'access': 'rw',
                    'offset': 0x10CFC
                },
                'P1ROWTAR8': {
                    'access': 'rw',
                    'offset': 0x10D00
                },
                'P1ROWTEAR8': {
                    'access': 'rw',
                    'offset': 0x10D04
                },
                'P1ROWBAR8': {
                    'access': 'rw',
                    'offset': 0x10D08
                },
                'P1ROWAR8': {
                    'access': 'rw',
                    'offset': 0x10D10
                },
                'P1ROWS1R8': {
                    'access': 'rw',
                    'offset': 0x10D14
                },
                'P1ROWS2R8': {
                    'access': 'rw',
                    'offset': 0x10D18
                },
                'P1ROWS3R8': {
                    'access': 'rw',
                    'offset': 0x10D1C
                },
                'P1RIWTAR4': {
                    'access': 'rw',
                    'offset': 0x10D60
                },
                'P1RIWBAR4': {
                    'access': 'rw',
                    'offset': 0x10D68
                },
                'P1RIWAR4': {
                    'access': 'rw',
                    'offset': 0x10D70
                },
                'P1RIWTAR3': {
                    'access': 'rw',
                    'offset': 0x10D80
                },
                'P1RIWBAR3': {
                    'access': 'rw',
                    'offset': 0x10D88
                },
                'P1RIWAR3': {
                    'access': 'rw',
                    'offset': 0x10D90
                },
                'P1RIWTAR2': {
                    'access': 'rw',
                    'offset': 0x10DA0
                },
                'P1RIWBAR2': {
                    'access': 'rw',
                    'offset': 0x10DA8
                },
                'P1RIWAR2': {
                    'access': 'rw',
                    'offset': 0x10DB0
                },
                'P1RIWTAR1': {
                    'access': 'rw',
                    'offset': 0x10DC0
                },
                'P1RIWBAR1': {
                    'access': 'rw',
                    'offset': 0x10DC8
                },
                'P1RIWAR1': {
                    'access': 'rw',
                    'offset': 0x10DD0
                },
                'P1RIWTAR0': {
                    'access': 'rw',
                    'offset': 0x10DE0
                },
                'P1RIWAR0': {
                    'access': 'rw',
                    'offset': 0x10DF0
                },
                'P2ROWTAR0': {
                    'access': 'rw',
                    'offset': 0x10E00
                },
                'P2ROWTEAR0': {
                    'access': 'rw',
                    'offset': 0x10E04
                },
                'P2ROWAR0': {
                    'access': 'rw',
                    'offset': 0x10E10
                },
                'P2ROWTAR1': {
                    'access': 'rw',
                    'offset': 0x10E20
                },
                'P2ROWTEAR1': {
                    'access': 'rw',
                    'offset': 0x10E24
                },
                'P2ROWBAR1': {
                    'access': 'rw',
                    'offset': 0x10E28
                },
                'P2ROWAR1': {
                    'access': 'rw',
                    'offset': 0x10E30
                },
                'P2ROWS1R1': {
                    'access': 'rw',
                    'offset': 0x10E34
                },
                'P2ROWS2R1': {
                    'access': 'rw',
                    'offset': 0x10E38
                },
                'P2ROWS3R1': {
                    'access': 'rw',
                    'offset': 0x10E3C
                },
                'P2ROWTAR2': {
                    'access': 'rw',
                    'offset': 0x10E40
                },
                'P2ROWTEAR2': {
                    'access': 'rw',
                    'offset': 0x10E44
                },
                'P2ROWBAR2': {
                    'access': 'rw',
                    'offset': 0x10E48
                },
                'P2ROWAR2': {
                    'access': 'rw',
                    'offset': 0x10E50
                },
                'P2ROWS1R2': {
                    'access': 'rw',
                    'offset': 0x10E54
                },
                'P2ROWS2R2': {
                    'access': 'rw',
                    'offset': 0x10E58
                },
                'P2ROWS3R2': {
                    'access': 'rw',
                    'offset': 0x10E5C
                },
                'P2ROWTAR3': {
                    'access': 'rw',
                    'offset': 0x10E60
                },
                'P2ROWTEAR3': {
                    'access': 'rw',
                    'offset': 0x10E64
                },
                'P2ROWBAR3': {
                    'access': 'rw',
                    'offset': 0x10E68
                },
                'P2ROWAR3': {
                    'access': 'rw',
                    'offset': 0x10E70
                },
                'P2ROWS1R3': {
                    'access': 'rw',
                    'offset': 0x10E74
                },
                'P2ROWS2R3': {
                    'access': 'rw',
                    'offset': 0x10E78
                },
                'P2ROWS3R3': {
                    'access': 'rw',
                    'offset': 0x10E7C
                },
                'P2ROWTAR4': {
                    'access': 'rw',
                    'offset': 0x10E80
                },
                'P2ROWTEAR4': {
                    'access': 'rw',
                    'offset': 0x10E84
                },
                'P2ROWBAR4': {
                    'access': 'rw',
                    'offset': 0x10E88
                },
                'P2ROWAR4': {
                    'access': 'rw',
                    'offset': 0x10E90
                },
                'P2ROWS1R4': {
                    'access': 'rw',
                    'offset': 0x10E94
                },
                'P2ROWS2R4': {
                    'access': 'rw',
                    'offset': 0x10E98
                },
                'P2ROWS3R4': {
                    'access': 'rw',
                    'offset': 0x10E9C
                },
                'P2ROWTAR5': {
                    'access': 'rw',
                    'offset': 0x10EA0
                },
                'P2ROWTEAR5': {
                    'access': 'rw',
                    'offset': 0x10EA4
                },
                'P2ROWBAR5': {
                    'access': 'rw',
                    'offset': 0x10EA8
                },
                'P2ROWAR5': {
                    'access': 'rw',
                    'offset': 0x10EB0
                },
                'P2ROWS1R5': {
                    'access': 'rw',
                    'offset': 0x10EB4
                },
                'P2ROWS2R5': {
                    'access': 'rw',
                    'offset': 0x10EB8
                },
                'P2ROWS3R5': {
                    'access': 'rw',
                    'offset': 0x10EBC
                },
                'P2ROWTAR6': {
                    'access': 'rw',
                    'offset': 0x10EC0
                },
                'P2ROWTEAR6': {
                    'access': 'rw',
                    'offset': 0x10EC4
                },
                'P2ROWBAR6': {
                    'access': 'rw',
                    'offset': 0x10EC8
                },
                'P2ROWAR6': {
                    'access': 'rw',
                    'offset': 0x10ED0
                },
                'P2ROWS1R6': {
                    'access': 'rw',
                    'offset': 0x10ED4
                },
                'P2ROWS2R6': {
                    'access': 'rw',
                    'offset': 0x10ED8
                },
                'P2ROWS3R6': {
                    'access': 'rw',
                    'offset': 0x10EDC
                },
                'P2ROWTAR7': {
                    'access': 'rw',
                    'offset': 0x10EE0
                },
                'P2ROWTEAR7': {
                    'access': 'rw',
                    'offset': 0x10EE4
                },
                'P2ROWBAR7': {
                    'access': 'rw',
                    'offset': 0x10EE8
                },
                'P2ROWAR7': {
                    'access': 'rw',
                    'offset': 0x10EF0
                },
                'P2ROWS1R7': {
                    'access': 'rw',
                    'offset': 0x10EF4
                },
                'P2ROWS2R7': {
                    'access': 'rw',
                    'offset': 0x10EF8
                },
                'P2ROWS3R7': {
                    'access': 'rw',
                    'offset': 0x10EFC
                },
                'P2ROWTAR8': {
                    'access': 'rw',
                    'offset': 0x10F00
                },
                'P2ROWTEAR8': {
                    'access': 'rw',
                    'offset': 0x10F04
                },
                'P2ROWBAR8': {
                    'access': 'rw',
                    'offset': 0x10F08
                },
                'P2ROWAR8': {
                    'access': 'rw',
                    'offset': 0x10F10
                },
                'P2ROWS1R8': {
                    'access': 'rw',
                    'offset': 0x10F14
                },
                'P2ROWS2R8': {
                    'access': 'rw',
                    'offset': 0x10F18
                },
                'P2ROWS3R8': {
                    'access': 'rw',
                    'offset': 0x10F1C
                },
                'P2RIWTAR4': {
                    'access': 'rw',
                    'offset': 0x10F60
                },
                'P2RIWBAR4': {
                    'access': 'rw',
                    'offset': 0x10F68
                },
                'P2RIWAR4': {
                    'access': 'rw',
                    'offset': 0x10F70
                },
                'P2RIWTAR3': {
                    'access': 'rw',
                    'offset': 0x10F80
                },
                'P2RIWBAR3': {
                    'access': 'rw',
                    'offset': 0x10F88
                },
                'P2RIWAR3': {
                    'access': 'rw',
                    'offset': 0x10F90
                },
                'P2RIWTAR2': {
                    'access': 'rw',
                    'offset': 0x10FA0
                },
                'P2RIWBAR2': {
                    'access': 'rw',
                    'offset': 0x10FA8
                },
                'P2RIWAR2': {
                    'access': 'rw',
                    'offset': 0x10FB0
                },
                'P2RIWTAR1': {
                    'access': 'rw',
                    'offset': 0x10FC0
                },
                'P2RIWBAR1': {
                    'access': 'rw',
                    'offset': 0x10FC8
                },
                'P2RIWAR1': {
                    'access': 'rw',
                    'offset': 0x10FD0
                },
                'P2RIWTAR0': {
                    'access': 'rw',
                    'offset': 0x10FE0
                },
                'P2RIWAR0': {
                    'access': 'rw',
                    'offset': 0x10FF0
                },
                'OM0MR': {
                    'access': 'rw',
                    'offset': 0x13000
                },
                'OM0SR': {
                    'access': 'rw',
                    'offset': 0x13004
                },
                'EOM0DQDPAR': {
                    'access': 'rw',
                    'offset': 0x13008
                },
                'OM0DQDPAR': {
                    'access': 'rw',
                    'offset': 0x1300C
                },
                'EOM0SAR': {
                    'access': 'rw',
                    'offset': 0x13010
                },
                'OM0SAR': {
                    'access': 'rw',
                    'offset': 0x13014
                },
                'OM0DPR': {
                    'access': 'rw',
                    'offset': 0x13018
                },
                'OM0DATR': {
                    'access': 'rw',
                    'offset': 0x1301C
                },
                'OM0DCR': {
                    'access': 'rw',
                    'offset': 0x13020
                },
                'EOM0DQEPAR': {
                    'access': 'rw',
                    'offset': 0x13024
                },
                'OM0DQEPAR': {
                    'access': 'rw',
                    'offset': 0x13028
                },
                'OM0RETCR': {
                    'access': 'rw',
                    'offset': 0x1302C
                },
                'OM0MGR': {
                    'access': 'rw',
                    'offset': 0x13030
                },
                'OM0MLR': {
                    'access': 'rw',
                    'offset': 0x13034
                },
                'IM0MR': {
                    'access': 'rw',
                    'offset': 0x13060
                },
                'IM0SR': {
                    'access': 'rw',
                    'offset': 0x13064
                },
                'EIM0FQDPAR': {
                    'access': 'rw',
                    'offset': 0x13068
                },
                'IM0FQDPAR': {
                    'access': 'rw',
                    'offset': 0x1306C
                },
                'EIM0FQEPAR': {
                    'access': 'rw',
                    'offset': 0x13070
                },
                'IM0FQEPAR': {
                    'access': 'rw',
                    'offset': 0x13074
                },
                'IM0MIRIR': {
                    'access': 'rw',
                    'offset': 0x13078
                },
                'OM1MR': {
                    'access': 'rw',
                    'offset': 0x13100
                },
                'OM1SR': {
                    'access': 'rw',
                    'offset': 0x13104
                },
                'EOM1DQDPAR': {
                    'access': 'rw',
                    'offset': 0x13108
                },
                'OM1DQDPAR': {
                    'access': 'rw',
                    'offset': 0x1310C
                },
                'EOM1SAR': {
                    'access': 'rw',
                    'offset': 0x13110
                },
                'OM1SAR': {
                    'access': 'rw',
                    'offset': 0x13114
                },
                'OM1DPR': {
                    'access': 'rw',
                    'offset': 0x13118
                },
                'OM1DATR': {
                    'access': 'rw',
                    'offset': 0x1311C
                },
                'OM1DCR': {
                    'access': 'rw',
                    'offset': 0x13120
                },
                'EOM1DQEPAR': {
                    'access': 'rw',
                    'offset': 0x13124
                },
                'OM1DQEPAR': {
                    'access': 'rw',
                    'offset': 0x13128
                },
                'OM1RETCR': {
                    'access': 'rw',
                    'offset': 0x1312C
                },
                'OM1MGR': {
                    'access': 'rw',
                    'offset': 0x13130
                },
                'OM1MLR': {
                    'access': 'rw',
                    'offset': 0x13134
                },
                'IM1MR': {
                    'access': 'rw',
                    'offset': 0x13160
                },
                'IM1SR': {
                    'access': 'rw',
                    'offset': 0x13164
                },
                'EIM1FQDPAR': {
                    'access': 'rw',
                    'offset': 0x13168
                },
                'IM1FQDPAR': {
                    'access': 'rw',
                    'offset': 0x1316C
                },
                'EIM1FQEPAR': {
                    'access': 'rw',
                    'offset': 0x13170
                },
                'IM1FQEPAR': {
                    'access': 'rw',
                    'offset': 0x13174
                },
                'IM1MIRIR': {
                    'access': 'rw',
                    'offset': 0x13178
                },
                'ODMR': {
                    'access': 'rw',
                    'offset': 0x13400
                },
                'ODSR': {
                    'access': 'rw',
                    'offset': 0x13404
                },
                'ODDPR': {
                    'access': 'rw',
                    'offset': 0x13418
                },
                'ODDATR': {
                    'access': 'rw',
                    'offset': 0x1341C
                },
                'ODRETCR': {
                    'access': 'rw',
                    'offset': 0x1342C
                },
                'IDMR': {
                    'access': 'rw',
                    'offset': 0x13460
                },
                'IDSR': {
                    'access': 'rw',
                    'offset': 0x13464
                },
                'EIDQDPAR': {
                    'access': 'rw',
                    'offset': 0x13468
                },
                'IDQDPAR': {
                    'access': 'rw',
                    'offset': 0x1346C
                },
                'EIDQEPAR': {
                    'access': 'rw',
                    'offset': 0x13470
                },
                'IDQEPAR': {
                    'access': 'rw',
                    'offset': 0x13474
                },
                'IDMIRIR': {
                    'access': 'rw',
                    'offset': 0x13478
                },
                'IPWMR': {
                    'access': 'rw',
                    'offset': 0x134E0
                },
                'IPWSR': {
                    'access': 'rw',
                    'offset': 0x134E4
                },
                'EIPWQBAR': {
                    'access': 'rw',
                    'offset': 0x134E8
                },
                'IPWQBAR': {
                    'access': 'rw',
                    'offset': 0x134EC
                }
            }
        },
        # 'TLB': {
        #     'count': 2,
        #     'registers': {
        #         'tlb0': {
        #             'bits': 32,
        #             'count': (16),
        #             'is_tlb': True,
        #             'fields': {
        #             }
        #         },
        #         'tlb1': {
        #             'bits': 32,
        #             'count': (512),
        #             'is_tlb': True,
        #             'fields': {
        #             }
        #         }
        #     }
        # },
        'USB': {
            'base': [
                p2020_ccsrbar+0x22000
            ],
            'count': 1,
            'memory_mapped': True,
            'registers': {
                'ID': {
                    'access': 'r',
                    'offset': 0x0
                },
                'CAPLENGTH': {
                    'access': 'r',
                    'bits': 8,
                    'offset': 0x100
                },
                'HCIVERSION': {
                    'access': 'r',
                    'bits': 16,
                    'offset': 0x102
                },
                'HCSPARAMS': {
                    'access': 'r',
                    'offset': 0x104
                },
                'HCCPARAMS': {
                    'access': 'r',
                    'offset': 0x108
                },
                'DCIVERSION': {
                    'access': 'r',
                    'bits': 16,
                    'offset': 0x120
                },
                'DCCPARAMS': {
                    'access': 'r',
                    'offset': 0x124
                },
                'USBSTS': {
                    'access': 'rw',
                    'offset': 0x144
                },
                'USBINTR': {
                    'access': 'rw',
                    'offset': 0x148
                },
                'FRINDEX': {
                    'access': 'rw',
                    'offset': 0x14C
                },
                'PERIODICLISTBASE': {
                    'access': 'rw',
                    'offset': 0x154
                },
                'DEVICEADDR': {
                    'access': 'rw',
                    'offset': 0x154
                },
                'ASYNCLISTADDR': {
                    'access': 'rw',
                    'offset': 0x158
                },
                'ENDPOINTLISTADDR': {
                    'access': 'rw',
                    'offset': 0x158
                },
                'BURSTSIZE': {
                    'access': 'rw',
                    'offset': 0x160
                },
                'TXFILLTUNING': {
                    'access': 'rw',
                    'offset': 0x164
                },
                'ULPI_VIEWPORT': {
                    'access': 'rw',
                    'offset': 0x170
                },
                'CONFIGFLAG': {
                    'access': 'r',
                    'offset': 0x180
                },
                'PORTSC': {
                    'access': 'rw',
                    'offset': 0x184
                },
                'USBMODE': {
                    'access': 'rw',
                    'offset': 0x1A8
                },
                'ENDPTSETUPSTAT': {
                    'access': 'w1c',
                    'offset': 0x1AC
                },
                'ENDPOINTPRIME': {
                    'access': 'rw',
                    'offset': 0x1B0
                },
                'ENDPTFLUSH': {
                    'access': 'rw',
                    'offset': 0x1B4
                },
                'ENDPTSTATUS': {
                    'access': 'r',
                    'offset': 0x1B8
                },
                'ENDPTCOMPLETE': {
                    'access': 'w1c',
                    'offset': 0x1BC
                },
                'ENDPTCTRL0': {
                    'access': 'rw',
                    'offset': 0x1C0
                },
                'ENDPTCTRL1': {
                    'access': 'rw',
                    'offset': 0x1C4
                },
                'ENDPTCTRL2': {
                    'access': 'rw',
                    'offset': 0x1C8
                },
                'ENDPTCTRL3': {
                    'access': 'rw',
                    'offset': 0x1CC
                },
                'ENDPTCTRL4': {
                    'access': 'rw',
                    'offset': 0x1D0
                },
                'ENDPTCTRL5': {
                    'access': 'rw',
                    'offset': 0x1D4
                },
                'SNOOP1': {
                    'access': 'rw',
                    'offset': 0x400
                },
                'SNOOP2': {
                    'access': 'rw',
                    'offset': 0x404
                },
                'AGE_CNT_THRESH': {
                    'access': 'rw',
                    'offset': 0x408
                },
                'PRI_CTRL': {
                    'access': 'rw',
                    'offset': 0x40C
                },
                'SI_CTRL': {
                    'access': 'rw',
                    'offset': 0x410
                },
                'CONTROL': {
                    'access': 'rw',
                    'offset': 0x500
                }
            }
        }
    }
}

calculate_target_bits(devices)

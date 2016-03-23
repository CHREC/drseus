from targets import calculate_target_bits

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

targets = {
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
            #     'fields': [
            #         ['Implementer', [24, 31]],
            #         ['Variant', [20, 23]],
            #         ['Architecture', [16, 19]],
            #         ['Primary part number', [4, 15]],
            #         ['Revision', [0, 3]]
            #     ]
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
            #     'fields': [
            #         ['SBZ', [24, 31]],
            #         ['ILsize', [16, 23]],
            #         ['DLsize', [8, 15]],
            #         ['SBZ/UNP', [3, 7]],
            #         ['TLB_size', [1, 2]],
            #         ['nU', [0, 0]]
            #     ]
            # },
            # 'MPIDR': {
            #     'CP': 15,
            #     'Op1': 0,
            #     'CRn': 0,
            #     'CRm': 0,
            #     'Op2': 5,
            #     'access': 'r',
            #     'fields': [
            #         ['FMT', [31, 31]],
            #         ['U', [30, 30]],
            #         ['SBZ', [12, 29]],
            #         ['Cluster ID', [8, 11]],
            #         ['SBZ', [2, 7]],
            #         ['CPU ID', [0, 1]]
            #     ]
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
            #     'fields': [
            #         ['WT', [31, 31]],
            #         ['WB', [30, 30]],
            #         ['RA', [29, 29]],
            #         ['WA', [28, 28]],
            #         ['NumSets', [13, 27]],
            #         ['Associativity', [3, 12]],
            #         ['LineSize', [0, 2]]
            #     ]
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
                'fields': [
                    ['UNP/SBZ', [4, 31]],
                    ['Level', [1, 3]],
                    ['InD', [0, 0]]
                ]
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
                'fields': [
                    ['SBZ', [31, 31]],
                    ['TE', [30, 30]],
                    ['AFE', [29, 29]],
                    ['TRE', [28, 28]],
                    ['NMFI', [27, 27]],
                    ['RAZ/SBZP', [26, 26]],
                    ['EE', [25, 25]],
                    ['RAZ/WI', [24, 24]],
                    ['RAO/SBOP', [22, 23]],
                    ['RAZ/WI', [21, 21]],
                    ['RAZ/SBZP', [19, 20]],
                    ['RAO/SBOP', [18, 18]],
                    ['RAZ/WI', [17, 17]],
                    ['RAO/SBOP', [16, 16]],
                    ['RAZ/SBZP', [15, 15]],
                    ['RR', [14, 14]],
                    ['V', [13, 13]],
                    ['I', [12, 12]],
                    ['Z', [11, 11]],
                    ['SW', [10, 10]],
                    ['RAZ/SBZP', [7, 9]],
                    ['RAO/SBOP', [3, 6]],
                    ['C', [2, 2]],
                    ['A', [1, 1]],
                    ['M', [0, 0]]
                ]
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
                'fields': [
                    ['ASEDIS', [31, 31]],
                    ['D32DIS', [30, 30]],
                    ['RAZ/WI', [24, 29]],
                    ['cp11', [22, 23]],
                    ['cp10', [20, 21]],
                    ['RAZ/WI', [0, 19]]
                ]
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
                'fields': [
                    ['UNK/SBZP', [9, 31]],
                    ['VA', [8, 8]],
                    ['VI', [7, 7]],
                    ['VF', [6, 6]],
                    ['UNK/SBZP', [0, 5]]
                ]
            },
            'Power Control Register': {
                'CP': 15,
                'Op1': 0,
                'CRn': 15,
                'CRm': 0,
                'Op2': 0,
                'access': 'rw',
                'fields': [
                    ['Reserved', [11, 31]],
                    ['max_clk_latency', [8, 10]],
                    ['Reserved', [1, 7]],
                    ['Enable dynamic clock gating', [0, 0]]
                ]
            },
            'NEON Busy Register': {
                'CP': 15,
                'Op1': 0,
                'CRn': 15,
                'CRm': 1,
                'Op2': 0,
                'access': 'r',
                'fields': [
                    ['Reserved', [1, 31]],
                    ['NEON busy', [0, 0]]
                ]
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
                'fields': [
                    ['UNK/SBZP', [9, 31]],
                    ['AMO', [8, 8]],
                    ['IMO', [7, 7]],
                    ['IFO', [6, 6]],
                    ['UNK/SBZP', [0, 5]]
                ]
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
                'fields': [
                    ['Reserved', [2, 31]],
                    ['Secure User Non-invasive Debug Enable', [1, 1]],
                    ['Secure User Invasive Debug Enable', [0, 0]]
                ]
            },
            'NSACR': {
                'CP': 15,
                'Op1': 0,
                'CRn': 1,
                'CRm': 1,
                'Op2': 2,
                'access': 'rw',
                'fields': [
                    ['UNK/SBZP', [19, 31]],
                    ['NS_SMP', [18, 18]],
                    ['TL', [17, 17]],
                    ['PLE', [16, 16]],
                    ['NSASEDIS', [15, 15]],
                    ['NSD32DIS', [14, 14]],
                    ['UNK/SBZP', [12, 13]],
                    ['CP11', [11, 11]],
                    ['CP10', [10, 10]],
                    ['UNK/SBZP', [0, 9]]
                ]
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
            #     'fields': [
            #         ['RAZ', [21, 31]],
            #         ['PLE FIFO size', [16, 20]],
            #         ['RAZ', [1, 15]],
            #         ['Present', [0, 0]]
            #     ]
            # },
            # 'PLEASR': {
            #     'CP': 15,
            #     'Op1': 0,
            #     'CRn': 11,
            #     'CRm': 0,
            #     'Op2': 2,
            #     'access': 'r',
            #     'fields': [
            #         ['Reserved/RAZ', [1, 31]],
            #         ['R', [0, 0]]
            #     ]
            # },
            # 'PLEFSR': {
            #     'CP': 15,
            #     'Op1': 0,
            #     'CRn': 11,
            #     'CRm': 0,
            #     'Op2': 4,
            #     'access': 'r',
            #     'fields': [
            #         ['Reserved/RAZ/WI', [5, 31]],
            #         ['Available entries', [0, 4]]
            #     ]
            # },
            'PLEUAR': {
                'CP': 15,
                'Op1': 0,
                'CRn': 11,
                'CRm': 1,
                'Op2': 0,
                'access': 'rw',
                'fields': [
                    ['RAZ', [1, 31]],
                    ['U', [0, 0]]
                ]
            },
            'PLEPCR': {
                'CP': 15,
                'Op1': 0,
                'CRn': 11,
                'CRm': 1,
                'Op2': 1,
                'access': 'rw',
                'fields': [
                    ['RAZ', [30, 31]],
                    ['Block size mask', [16, 29]],
                    ['Block number mask', [8, 15]],
                    ['PLE wait states', [0, 7]]
                ]
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
                'fields': [
                    ['UNK/SBZP', [30, 31]],
                    ['Victim', [28, 29]],
                    ['UNK/SBZP', [1, 27]],
                    ['P', [0, 0]]
                ]
            },
            'Select Lockdown TLB Entry for read': {
                'CP': 15,
                'Op1': 5,
                'CRn': 15,
                'CRm': 4,
                'Op2': 2,
                'access': 'w',
                'fields': [
                    ['UNK/SBZP', [2, 31]],
                    ['Index', [0, 1]]
                ]
            },
            'Select Lockdown TLB Entry for write': {
                'CP': 15,
                'Op1': 5,
                'CRn': 15,
                'CRm': 4,
                'Op2': 4,
                'access': 'w',
                'fields': [
                    ['UNK/SBZP', [2, 31]],
                    ['Index', [0, 1]]
                ]
            },
            'Main TLB VA register': {
                'CP': 15,
                'Op1': 5,
                'CRn': 15,
                'CRm': 5,
                'Op2': 2,
                'access': 'rw',
                'fields': [
                    ['VPN', [12, 31]],
                    ['UNK/SBZP', [11, 11]],
                    ['NS', [10, 10]],
                    ['Process', [0, 9]]
                ]
            },
            'Main TLB PA register': {
                'CP': 15,
                'Op1': 5,
                'CRn': 15,
                'CRm': 6,
                'Op2': 2,
                'access': 'rw',
                'fields': [
                    ['PPN', [12, 31]],
                    ['UNK/SBZP', [8, 11]],
                    ['SZ', [6, 7]],
                    ['UNK/SBZP', [4, 5]],
                    ['AP', [1, 3]],
                    ['V', [0, 0]]
                ]
            },
            'Main TLB Attribute register': {
                'CP': 15,
                'Op1': 5,
                'CRn': 15,
                'CRm': 7,
                'Op2': 2,
                'access': 'rw',
                'fields': [
                    ['UNK/SBZP', [12, 31]],
                    ['NS', [11, 11]],
                    ['Domain', [7, 10]],
                    ['XN', [6, 6]],
                    ['TEX', [3, 5]],
                    ['CB', [1, 2]],
                    ['S', [0, 0]]
                ]
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
                'fields': [
                    ['UNP/SBZP', [10, 31]],
                    ['Parity on', [9, 9]],
                    ['Alloc in one way', [8, 8]],
                    ['EXCL', [7, 7]],
                    ['SMP', [6, 6]],
                    ['RAZ/WI', [4, 5]],
                    ['Write full line of zeros mode', [3, 3]],
                    ['L1 prefetch enable', [2, 2]],
                    ['L2 prefetch enable', [1, 1]],
                    ['FW', [0, 0]]
                ]
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
            #     'fields': [
            #         ['Arch', [28, 31]],
            #         ['Design', [20, 27]],
            #         ['SArchMajor', [12, 19]],
            #         ['SArchMinor', [8, 11]],
            #         ['RAZ', [7, 7]],
            #         ['TrTbleFrm', [6, 6]],
            #         ['TrTbleSz', [0, 5]]
            #     ]
            # },
            'JOSCR': {
                'CP': 14,
                'Op1': 7,
                'CRn': 1,
                'CRm': 0,
                'Op2': 0,
                'access': 'rw',
                'fields': [
                    ['Reserved/RAZ', [2, 31]],
                    ['CV', [1, 1]],
                    ['CD', [0, 0]]
                ]
            },
            'JMCR': {
                'CP': 14,
                'Op1': 7,
                'CRn': 2,
                'CRm': 0,
                'Op2': 0,
                'access': 'rw',
                'fields': [
                    ['nAR', [31, 31]],
                    ['FP', [30, 30]],
                    ['AP', [29, 29]],
                    ['OP', [28, 28]],
                    ['IS', [27, 27]],
                    ['SP', [26, 26]],
                    ['UNK/SBZP', [1, 25]],
                    ['JE', [0, 0]]
                ]
            },
            'Jazelle Parameters Register': {
                'CP': 14,
                'Op1': 7,
                'CRn': 3,
                'CRm': 0,
                'Op2': 0,
                'access': 'rw',
                'fields': [
                    ['UNK/SBZP', [22, 31]],
                    ['BSH', [17, 21]],
                    ['sADO', [12, 16]],
                    ['ARO', [8, 11]],
                    ['STO', [4, 7]],
                    ['ODO', [0, 3]]
                ]
            },
            'Jazelle Configurable Opcode Translation Table Register': {
                'CP': 14,
                'Op1': 7,
                'CRn': 4,
                'CRm': 0,
                'Op2': 0,
                'access': 'w',
                'fields': [
                    ['UNK/SBZP', [16, 31]],
                    ['Opcode', [10, 15]],
                    ['UNK/SBZP', [4, 9]],
                    ['Operation', [0, 3]]
                ]
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
}

calculate_target_bits(targets)

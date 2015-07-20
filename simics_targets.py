# if count is not present it is assumed to be 1
# if bits is not present it is assumbed to be 32
# bits are listed as MSB:0 LSB:31 hence 31-i in bit ranges
# 32-bit CPU register bits are listed as MSB:32 LSB:63 hence 63-i in bit ranges
devices = {
    'a9x2': {
        'CPU': {
            'count': 2,
            'OBJECT': '.coretile.mpcore.core',
            'TYPE': 'arm-cortex-a9',
            'registers': {
                'cpsr': {},
                'spsr': {
                    'count': (7, ),
                },
            },
        },
        'GPR': {
            'count': 2,
            'OBJECT': '.coretile.mpcore.core',
            'TYPE': 'arm-cortex-a9',
            'registers': {
                'gprs': {
                    'count': (7, 16),
                }
            }
        }
    },
    'p2020rdb': {
        'CCSR': {
            # LIMITATIONS: ALTCBAR and ALTCAR registers are unsupported.
            #              Interleaved SDRAM mappings are instead mapped
            #              sequentially.
            'OBJECT': '.soc.ccsr',
            'TYPE': 'qoriq-p2-ccsr',
            'registers': {
                'LAWAR': {
                    'count': (12, )
                },
                'LAWBAR': {
                    'count': (12, )
                },
                'CCSRBAR': {},
                'BPTR': {}
                # Not Implemented
                # 'ALTCAR': {},
                # 'ALTCBAR': {}
            }
        },
        'CPU': {
            'count': 2,
            'OBJECT': '.soc.cpu',
            'TYPE': 'ppce500',
            'registers': {
                'pc': {},
                'l1cfg0': {},
                'l1cfg1': {},
                'cr': {},
                'ctr': {},
                'lr': {},
                'xer': {},
                'spefscr': {},
                'usprg0': {},
                'sprg3': {},
                'sprg4': {},
                'sprg5': {},
                'sprg6': {},
                'sprg7': {},
                'tbl': {},
                'tbu': {},
                'atbl': {},
                'atbu': {},
                'acc': {
                    'bits': 64
                },
                'ivpr': {},
                'srr0': {},
                'srr1': {},
                'csrr0': {},
                'csrr1': {},
                'mcsrr0': {},
                'mcsrr1': {},
                'esr': {},
                'mcsr': {},
                'mcar': {},
                'dear': {},
                'ivor0': {},
                'ivor1': {},
                'ivor2': {},
                'ivor3': {},
                'ivor4': {},
                'ivor5': {},
                'ivor6': {},
                'ivor7': {},
                'ivor8': {},
                'ivor9': {},
                'ivor10': {},
                'ivor11': {},
                'ivor12': {},
                'ivor13': {},
                'ivor14': {},
                'ivor15': {},
                'ivor32': {},
                'ivor33': {},
                'ivor34': {},
                'ivor35': {},
                'dbcr0': {},
                'dbcr1': {},
                'dbcr2': {},
                'dbsr': {},
                'iac1': {},
                'iac2': {},
                'dac1': {},
                'dac2': {},
                'mmucsr0': {},
                'mas0': {},
                'mas1': {},
                'mas2': {},
                'mas3': {},
                'mas4': {},
                'mas6': {},
                'mas7': {},
                'pid0': {},
                'pid1': {},
                'pid2': {},
                'mmucfg': {},
                'tlb0cfg': {},
                'tlb1cfg': {},
                'l1csr0': {},
                'l1csr1': {},
                'msr': {},
                'svr': {},
                'pir': {},
                'pvr': {},
                'dec': {},
                'decar': {},
                'tcr': {},
                'tsr': {},
                'hid0': {},
                'hid1': {},
                'sprg0': {},
                'sprg1': {},
                'sprg2': {},
                'pmgc0': {},
                'pmc0': {},
                'pmc1': {},
                'pmc2': {},
                'pmc3': {},
                'pmlca0': {},
                'pmlca1': {},
                'pmlca2': {},
                'pmlca3': {},
                'pmlcb0': {},
                'pmlcb1': {},
                'pmlcb2': {},
                'pmlcb3': {},
                'iarr': {},  # not found in P2020 docs
                # extra performance monitor counter registers
                # (not found in P2020 docs)
                'pmc4': {},
                'pmc5': {},
                'pmc6': {},
                'pmc7': {},
                'pmc8': {},
                'pmc9': {},
                'pmc10': {},
                'pmc11': {},
                'pmc12': {},
                'pmc13': {},
                'pmc14': {},
                'pmc15': {},
                'pmlca4': {},
                'pmlca5': {},
                'pmlca6': {},
                'pmlca7': {},
                'pmlca8': {},
                'pmlca9': {},
                'pmlca10': {},
                'pmlca11': {},
                'pmlca12': {},
                'pmlca13': {},
                'pmlca14': {},
                'pmlca15': {},
                'pmlcb4': {},
                'pmlcb5': {},
                'pmlcb6': {},
                'pmlcb7': {},
                'pmlcb8': {},
                'pmlcb9': {},
                'pmlcb10': {},
                'pmlcb11': {},
                'pmlcb12': {},
                'pmlcb13': {},
                'pmlcb14': {},
                'pmlcb15': {}
                # Not Implemented
                # 'npidr1': {},
                # 'bbear': {},
                # 'bbtar': {},
                # 'bucsr': {},
                # 'hdbcr0': {},
                # 'hdbcr1': {},
                # 'hdbcr5': {}
                # 'upmgc0': {},
                # 'upmc0': {},
                # 'upmc1': {},
                # 'upmc2': {},
                # 'upmc3': {},
                # 'upmlca0': {},
                # 'upmlca1': {},
                # 'upmlca2': {},
                # 'upmlca3': {},
                # 'upmlcb0': {},
                # 'upmlcb1': {},
                # 'upmlcb2': {},
                # 'upmlcb3': {}
            },
        },
        'GPR': {
            'count': 2,
            'OBJECT': '.soc.cpu',
            'TYPE': 'ppce500',
            'registers': {
                'gprs': {
                    'count': (32, ),
                    'bits': 64
                }
            }
        },
        'TLB': {
            'count': 2,
            'OBJECT': '.soc.cpu',
            'TYPE': 'ppce500',
            'registers': {
                'tlb0': {
                    'is_tlb': True,
                    'bits': 77,
                    'count': (128, 4, 5),
                    'fields': {
                        'V': {
                            'bits': 1,
                            'index': 1,
                            'bit_indicies': (63-32, 63-32)
                        },
                        'TS': {
                            'bits': 1,
                            'index': 1,
                            'bit_indicies': (63-51, 63-51)
                        },
                        'TID': {
                            'bits': 8,
                            'index': 1,
                            'bit_indicies': (63-47, 63-40)
                        },
                        'EPN': {
                            'bits': 20,
                            'index': 2,
                            'bit_indicies': (63-51, 63-32)
                        },
                        'RPN': {
                            'bits': 24,
                            'split': True,
                            'bits_h': 4,
                            'bits_l': 20,
                            'index_h': 4,
                            'index_l': 3,
                            'bit_indicies_h': (63-63, 63-60),
                            'bit_indicies_l': (63-51, 63-32)
                        },
                        'SIZE': {
                            'bits': 4,
                            'index': 1,
                            'bit_indicies': (63-55, 63-52)
                        },
                        'UX': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-58, 63-58)
                        },
                        'SX': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-59, 63-59)
                        },
                        'UW': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-60, 63-60)
                        },
                        'SW': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-61, 63-61)
                        },
                        'UR': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-62, 63-62)
                        },
                        'SR': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-63, 63-63)
                        },
                        'W': {
                            'bits': 1,
                            'index': 2,
                            'bit_indicies': (63-59, 63-59)
                        },
                        'I': {
                            'bits': 1,
                            'index': 2,
                            'bit_indicies': (63-60, 63-60)
                        },
                        'M': {
                            'bits': 1,
                            'index': 2,
                            'bit_indicies': (63-61, 63-61)
                        },
                        'G': {
                            'bits': 1,
                            'index': 2,
                            'bit_indicies': (63-62, 63-62)
                        },
                        'E': {
                            'bits': 1,
                            'index': 2,
                            'bit_indicies': (63-63, 63-63)
                        },
                        'X': {
                            'bits': 2,
                            'index': 2,
                            'bit_indicies': (63-58, 63-57)
                        },
                        'U': {
                            'bits': 4,
                            'index': 3,
                            'bit_indicies': (63-57, 63-54)
                        },
                        'NV': {
                            'bits': 2,
                            'index': 0,
                            'bit_indicies': (63-63, 63-62)
                        }
                    }
                },
                'tlb1': {
                    'is_tlb': True,
                    'bits': 76,
                    'count': (16, 5),
                    'fields': {
                        'V': {
                            'bits': 1,
                            'index': 1,
                            'bit_indicies': (63-32, 63-32)
                        },
                        'TS': {
                            'bits': 1,
                            'index': 1,
                            'bit_indicies': (63-51, 63-51)
                        },
                        'TID': {
                            'bits': 8,
                            'index': 1,
                            'bit_indicies': (63-47, 63-40)
                        },
                        'EPN': {
                            'bits': 20,
                            'index': 2,
                            'bit_indicies': (63-51, 63-32)
                        },
                        'RPN': {
                            'bits': 24,
                            'split': True,
                            'bits_h': 4,
                            'bits_l': 20,
                            'index_h': 4,
                            'index_l': 3,
                            'bit_indicies_h': (63-63, 63-60),
                            'bit_indicies_l': (63-51, 63-32)
                        },
                        'SIZE': {
                            'bits': 4,
                            'index': 1,
                            'bit_indicies': (63-55, 63-52)
                        },
                        'UX': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-58, 63-58)
                        },
                        'SX': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-59, 63-59)
                        },
                        'UW': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-60, 63-60)
                        },
                        'SW': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-61, 63-61)
                        },
                        'UR': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-62, 63-62)
                        },
                        'SR': {
                            'bits': 1,
                            'index': 3,
                            'bit_indicies': (63-63, 63-63)
                        },
                        'W': {
                            'bits': 1,
                            'index': 2,
                            'bit_indicies': (63-59, 63-59)
                        },
                        'I': {
                            'bits': 1,
                            'index': 2,
                            'bit_indicies': (63-60, 63-60)
                        },
                        'M': {
                            'bits': 1,
                            'index': 2,
                            'bit_indicies': (63-61, 63-61)
                        },
                        'G': {
                            'bits': 1,
                            'index': 2,
                            'bit_indicies': (63-62, 63-62)
                        },
                        'E': {
                            'bits': 1,
                            'index': 2,
                            'bit_indicies': (63-63, 63-63)
                        },
                        'X': {
                            'bits': 2,
                            'index': 2,
                            'bit_indicies': (63-58, 63-57)
                        },
                        'U': {
                            'bits': 4,
                            'index': 3,
                            'bit_indicies': (63-57, 63-54)
                        },
                        'IPROT': {
                            'bits': 1,
                            'index': 1,
                            'bit_indicies': (63-33, 63-33)
                        }
                    }
                }
            }
        },
        'DMA': {
            # LIMITATIONS: The DMA pause feature and DMA halt features have
            #              not been implemented.
            'count': 2,
            'OBJECT': '.soc.dma',
            'TYPE': 'qoriq-p2-dma',
            'registers': {
                'BCR': {
                    'count': (4, )
                },
                'CLNDAR': {
                    'count': (4, )
                },
                'CLSDAR': {
                    'count': (4, )
                },
                'DAR': {
                    'count': (4, )
                },
                'DATR': {
                    'count': (4, ),
                    'bits': 28,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved3': (31-0, 31-0),
                        'NLWR': (31-1, 31-1),
                        'Reserved2': (31-6, 31-2),
                        'DSME': (31-7, 31-7),
                        'Reserved1': (31-11, 31-8),
                        # Not Implemented
                        # 'DWRITETTYPE': (31-15, 31-12),
                        'Reserved0': (31-31, 31-16)
                        # Not Implemented: DPCI_ORDER, DTFLOWLVL, DTRANSINT
                    },
                },
                # Pseudo register, not present in Simics checkpoint config files
                # P2020 docs say this is just a combination of other channel
                # status bits
                # 'DGSR': {},
                'DSR': {
                    'count': (4, )
                },
                'ECLNDAR': {
                    'count': (4, )
                },
                'ECLSDAR': {
                    'count': (4, )
                },
                'ENLNDAR': {
                    'count': (4, )
                },
                'ENLSDAR': {
                    'count': (4, )
                },
                'MR': {
                    'count': (4, ),
                    'bits': 30,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved3': (31-3, 31-0),
                        'BWC': (31-7, 31-4),
                        'Reserved2': (31-9, 31-8),
                        # Not Implemented
                        # 'EMP_EN': (31-10, 31-10),
                        'Reserved1': (31-12, 31-11),
                        'EMS_EN': (31-13, 31-13),
                        'DAHTS': (31-15, 31-14),
                        'SAHTS': (31-17, 31-16),
                        'DAHE': (31-18, 31-18),
                        'SAHE': (31-19, 31-19),
                        'Reserved0': (31-20, 31-20),
                        'SRW': (31-21, 31-21),
                        'EOSIE': (31-22, 31-22),
                        'EOLINE': (31-23, 31-23),
                        'EOLSIE': (31-24, 31-24),
                        'EIE': (31-25, 31-25),
                        'XFE': (31-26, 31-26),
                        'CDSM_SWSM': (31-27, 31-27),
                        'CA': (31-28, 31-28),
                        'CTM': (31-29, 31-29),
                        'CC': (31-30, 31-30)
                        # Not Implemented
                        # 'CS': (31-31, 31-31)
                    },
                },
                'NLDAR': {
                    'count': (4, )
                },
                'NLNDAR': {
                    'count': (4, )
                },
                'NLSDAR': {
                    'count': (4, )
                },
                'SAR': {
                    'count': (4, )
                },
                'SATR': {
                    'count': (4, ),
                    'bits': 28,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved2': (31-6, 31-0),
                        'SSME': (31-7, 31-7),
                        'Reserved1': (31-11, 31-8),
                        # Not Implemented
                        # 'SREADTTYPE': (31-15, 31-12),
                        'Reserved0': (31-31, 31-16)
                        # Not Implemented: SPCI_ORDER, STFLOWLVL, STRANSIT
                    },
                },
                'SR': {
                    'count': (4, )
                },
                'SSR': {
                    'count': (4, )
                }
            }
        },
        'ECM': {
            # LIMITATIONS: Handles enabling/disabling the cores only.
            #              Access errors are not monitored nor reported.
            'OBJECT': '.soc.ecm',
            'TYPE': 'qoriq-p2-ecm',
            'registers': {
                'EEBPCR': {}
                # Not Implemented
                # 'EEATR': {},
                # 'EEBACR': {},
                # 'EEDR': {},
                # 'EEER': {},
                # 'EEHADR': {},
                # 'EELADR': {},
                # 'ECMIP_REV1': {},
                # 'ECMIP_REV2': {}
            }
        },
        'ELBC': {
            'OBJECT': '.soc.elbc',
            'TYPE': 'qoriq-p2-elbc',
            'registers': {
                'BR': {
                    'count': (8, )
                },
                'OR': {
                    'count': (8, )
                },
                'FBAR': {},
                'FBCR': {},
                'FCR': {},
                'FECC': {
                    'count': (4, )
                },
                'FIR': {},
                'FMR': {},
                'FPAR': {},
                'LBCR': {
                    'bits': 15,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'LDIS': (31-0, 31-0),
                        'Reserved2': (31-7, 31-1),
                        # Not Implemented
                        # 'BCTLC': (31-9, 31-8),
                        # 'AHD': (31-10, 31-10),
                        'Reserved1': (31-13, 31-11),
                        # Not Implemented
                        # 'LPBSE': (31-14, 31-14),
                        # 'EPAR': (31-15, 31-15),
                        # 'BMT': (31-23, 31-16),
                        'Reserved0': (31-27, 31-24),
                        # Not Implemented
                        # 'BMTPS': (31-31, 31-28)
                    },
                },
                'LCRR': {
                    'bits': 25,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'PBYP': (31-0, 31-0),
                        'Reserved1': (31-13, 31-1),
                        # Not Implemented
                        # 'EADC': (31-15, 31-14),
                        'Reserved0': (31-26, 31-16),
                        # Not Implemented
                        # 'CLKDIV': (31-31, 31-27)
                    },
                },
                'LSOR': {},
                'LTEAR': {},
                'LTEATR': {},
                'LTECCR': {},
                'LTEDR': {},
                'LTEIR': {},
                'LTESR': {},
                'LURT': {},
                'MAMR': {},
                'MAR': {},
                'MBMR': {},
                'MCMR': {},
                'MDR': {},
                'MRTPR': {}
            }
        },
        'ESDHC': {
            # LIMITATIONS: PIO mode not implemented (i.e. DMA must be used).
            #              Command and Data CRC check is not supported.
            #              Infinite data transfers not supported.
            'OBJECT': '.soc.esdhc',
            'TYPE': 'qoriq-p2-esdhc',
            'registers': {
                'regs_ADMAES': {},
                'regs_ADMASA': {
                    'count': (2, )
                },
                'regs_AUTOC12ERR': {},
                'regs_BLKATTR': {},
                'regs_CMDARG': {},
                'regs_CMDRSP': {
                    'count': (4, )
                },
                # 'regs_DATPORT': {},
                'regs_DCR': {
                    'bits': 28,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved2': (31-15, 31-0),
                        'PRI': (31-17, 31-16),
                        'Reserved1': (31-24, 31-18),
                        # Not Implemented
                        # 'SNOOP': (31-25, 31-25),
                        'Reserved0': (31-28, 31-26),
                        # Not Implemented
                        # 'RD_SAFE': (31-29, 31-29),
                        # 'RD_PFE': (31-30, 31-30),
                        # 'RD_PF_SIZE': (31-31, 31-31)
                    }
                },
                'regs_DSADDR': {},
                'regs_HOSTCAPBLT': {},
                'regs_HOSTVER': {},
                'regs_IRQSIGEN': {},
                'regs_IRQSTAT': {},
                'regs_IRQSTATEN': {},
                'regs_MAXCUR': {
                    'count': (2, )
                },
                'regs_PROCTL': {
                    'bits': 22,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        # Field IABG - Not implemented.
                        # Field WECINT - Not implemented.
                        'Reserved3': (31-4, 31-0),
                        # Not Implemented
                        # 'WECRM': (31-5, 31-5),
                        # 'WECINS': (31-6, 31-6),
                        'Reserved2': (31-12, 31-7),
                        # Not Implemented
                        # 'RWCTL': (31-13, 31-13),
                        # 'CREQ': (31-14, 31-14),
                        # 'SABGREQ': (31-15, 31-15),
                        'Reserved1': (31-23, 31-16),
                        # Not Implemented
                        # 'CDSS': (31-24, 31-24),
                        # 'CDTL': (31-25, 31-25),
                        'EMODE': (31-27, 31-26),
                        # Not Implemented
                        # 'D3CD': (31-28, 31-28),
                        # 'DTW': (31-30, 31-29),
                        'Reserved0': (31-31, 31-31)
                    }
                },
                'regs_PRSSTAT': {},
                'regs_SYSCTL': {
                    'bits': 12,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved2': (31-3, 31-0),
                        # Not Implemented
                        # 'INITA': (31-4, 31-4),
                        'RSTD': (31-5, 31-5),
                        'RSTC': (31-6, 31-6),
                        'RSTA': (31-7, 31-7),
                        'Reserved1': (31-11, 31-8),
                        # Not Implemented
                        # 'DTOCV': (31-15, 31-12),
                        # 'SDCLKFS': (31-23, 31-16),
                        # 'DVS': (31-27, 31-24),
                        'Reserved0': (31-28, 31-28),
                        # Not Implemented
                        # 'PEREN': (31-29, 31-29),
                        # 'HCKEN': (31-30, 31-30),
                        # 'IPGEN': (31-31, 31-31)
                    }
                },
                'regs_WML': {
                    'bits': 16,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved1': (31-7, 31-0),
                        # Not Implemented
                        # 'WR_WML': (31-15, 31-8),
                        'Reserved0': (31-23, 31-16),
                        # Not Implemented
                        # 'RD_WML': (31-31, 31-24)
                    }
                },
                'regs_XFERTYP': {
                    'bits': 30,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved3': (31-1, 31-0),
                        'CMDINX': (31-7, 31-2),
                        # Not Implemented
                        # 'CMDTYP': (31-9, 31-8),
                        'DPSEL': (31-10, 31-10),
                        'CICEN': (31-11, 31-11),
                        'CCCEN': (31-12, 31-12),
                        'Reserved2': (31-13, 31-13),
                        'RSPTYP': (31-15, 31-14),
                        'Reserved1': (31-25, 31-16),
                        'MSBSEL': (31-26, 31-26),
                        'DTDSEL': (31-27, 31-27),
                        'Reserved0': (31-28, 31-28),
                        'AC12EN': (31-29, 31-29),
                        'BCEN': (31-30, 31-30),
                        'DMAEN': (31-31, 31-31)
                    }
                },
            }
        },
        'ESPI': {
            # LIMITATIONS: Dual Output and RapidS are both unimplemented
            #              Transmission speed settings are unimplemented.
            #              When the throttle attribute is set, 3.125 Mbit is
            #              used as an upper bound for the bitrate.
            'OBJECT': '.soc.espi',
            'TYPE': 'qoriq-p2-espi',
            'registers': {
                'regs_CS_SPMODE': {
                    'count': (4, ),
                    'bits': 12,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'CI': (31-0, 31-0),
                        'CP': (31-1, 31-1),
                        'REV': (31-2, 31-2),
                        # Not Implemented
                        # 'DIV16': (31-3, 31-3),
                        # 'PM': (31-7, 31-4),
                        # 'ODD': (31-8, 31-8),
                        'Reseved1': (31-10, 31-9),
                        # Not Implemented
                        # 'POL': (31-11, 31-11),
                        'LEN': (31-15, 31-12),
                        # Not Implemented
                        # 'CSBEF': (31-19, 31-16),
                        # 'CSAFT': (31-23, 31-20),
                        # 'CSCG': (31-28, 31-24),
                        'Reserved0': (31-31, 31-29)
                    }
                },
                'regs_SPCOM': {
                    'fields': {
                        'CS': (31-1, 31-0),
                        'RxDelay': (31-2, 21-2),
                        'DO': (31-3, 31-3),  # Write-access not implemented
                        'TO': (31-4, 31-4),
                        'HLD': (31-5, 31-5),
                        'Reserved': (31-7, 31-6),
                        'RxSKIP': (31-15, 31-8),
                        'TRANLEN': (31-31, 31-16)
                    }
                },
                'regs_SPIE': {},
                'regs_SPIM': {},
                'regs_SPMODE': {}
            }
        },
        'ETSEC': {
            # LIMITATIONS: Huge frames, interrupt coalescing, statistics
            #              counters, lossless flow control and timer related
            #              functions are not implemented. Only RXF interrupt is
            #              generated when receiving buffers.
            'count': 3,
            'OBJECT': '.soc.etsec',
            'TYPE': 'qoriq-p2-etsec',
            'registers': {
                'ATTR': {},
                'ATTRELI': {},
                'CAM1': {},
                'CAM2': {},
                'DFVLAN': {},
                'DMACTRL': {
                    'bits': 30,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved2': (31-15, 31-0),
                        'LE': (31-16, 31-16),
                        'Reserved1': (31-23, 31-17),
                        'TDSEN': (31-24, 31-24),
                        'TBDSEN': (31-25, 31-25),
                        'Reserved0': (31-26, 31-26),
                        'GRS': (31-27, 31-27),
                        'GTS': (31-28, 31-28),  # Tx is not restarted
                                                # when cleared
                        # Not Implemented
                        # 'TOD': (31-29, 31-29),
                        # 'WWR': (31-30, 31-30),
                        'WOP': (31-31, 31-31)
                    }
                },
                'ECNTRL': {
                    'bits': 28,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved2': (31-16, 31-0),
                        # Not Implemented
                        # 'CLRCNT': (31-17, 31-17),
                        # 'AUTOZ': (31-18, 31-18),
                        # 'STEN': (31-19, 31-19),
                        'Reserved1': (31-24, 31-20),
                        'GMIIM': (31-25, 31-25),
                        'TBIM': (31-26, 31-26),
                        'RPM': (31-27, 31-27),
                        # Not Implemented
                        # 'R100M': (31-28, 31-28),
                        'RMM': (31-29, 31-29),
                        'SGMIIM': (31-30, 31-30),
                        'Reserved0': (31-31, 31-31)
                    }
                },
                'EDIS': {},
                'FIFO_TX_STARVE': {},
                'FIFO_TX_STARVE_SHUTOFF': {},
                'FIFO_TX_THR': {},
                'GADDR': {
                    'count': (8, )
                },
                'HAFDUP': {},
                'IADDR': {
                    'count': (8, )
                },
                'IEVENT': {},
                'IFSTAT': {},
                'IMASK': {},
                'IPGIFGI': {},
                'MACCFG1': {
                    'bits': 23,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        # Not Implemented
                        # 'Soft_Reset': (31-0, 31-0),
                        'Reserved2': (31-11, 31-1),
                        # Not Implemented
                        # 'Reset_Rx_MC': (31-12, 31-12),
                        # 'Reset_Tx_MC': (31-13, 31-13),
                        # 'Reset_Rx_Fun': (31-14, 31-14),
                        # 'Reset_Tx_Fun': (31-15, 31-15),
                        'Reserved1': (31-22, 31-16),
                        'Loop_Back': (31-23, 31-23),
                        'Reserved0': (31-25, 31-24),
                        # Not Implemented
                        # 'Rx_Flow': (31-26, 31-26),
                        # 'Tx_Flow': (31-27, 31-27),
                        # 'Syncd_Rx_EN': (31-28, 31-28),
                        'Rx_EN': (31-29, 31-29),
                        # Not Implemented
                        # 'Syncd_Tx_EN': (31-30, 31-30),
                        'Tx_EN': (31-31, 31-31)
                    }
                },
                'MACCFG2': {
                    'bits': 29,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved1': (31-15, 31-0),
                        'Preamble_Length': (31-19, 31-16),
                        'Reserved0': (31-21, 31-20),
                        'I_F_Mode': (31-23, 31-22),
                        'PreAM_RxEN': (31-24, 31-24),
                        'PreAM_TxEN': (31-25, 31-25),
                        # Not Implemented
                        # 'Huge_Frame': (31-26, 31-26),
                        # 'Length_Check': (31-27, 31-27),
                        'MPEN': (31-28, 31-28),
                        'PAD_CRC': (31-29, 31-29),
                        'CRC_EN': (31-30, 31-30),
                        # Not Implemented
                        # 'Full_Duplex': (31-31, 31-31)
                    }
                },
                'MACSTNADDR1': {},
                'MACSTNADDR2': {},
                'MAC_ADD1': {
                    'count': (15, )
                },
                'MAC_ADD2': {
                    'count': (15, )
                },
                'MAXFRM': {},
                'MIIMADD': {},
                'MIIMCFG': {
                    'bits': 27,
                    'fields': {
                        # Not Implemented
                        # 'Reset_Mgmt': (31-0, 31-0),
                        'Reserved1': (31-36, 31-1),
                        # Not Implemented
                        # 'No_Pre': (31-27, 31-27),
                        'Reserved0': (31-28, 31-28),
                        # Not Implemented
                        # 'MgmtClk': (31-31, 31-29)
                    }
                },
                'MIIMCOM': {},
                'MIIMCON': {},
                'MIIMIND': {},
                'MIIMSTAT': {},
                'MINFLR': {},
                'MRBLR': {},
                'PTV': {},
                'RALN': {},
                'RBASE': {
                    'count': (8, )
                },
                'RBASEH': {},
                'RBCA': {},
                'RBDBPH': {},
                'RBIFX': {},
                'RBPTR': {
                    'count': (8, )
                },
                'RBYT': {},
                'RCDE': {},
                'RCSE': {},
                'RCTRL': {
                    'bits': 30,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        # Field CFA - Not implemented.
                        'L2OFF': (31-6, 31-0),
                        # Not Implemented
                        # 'TS': (31-7, 31-7),
                        'Reserved3': (31-10, 31-8),
                        'PAL': (31-15, 31-11),
                        'Reserved2': (31-16, 31-16),
                        # Not Implemented
                        # 'LFC': (31-17, 31-17),
                        'VLEX': (31-18, 31-18),
                        'FILREN': (31-19, 31-19),
                        'FSQEN': (31-20, 31-20),
                        'GHTX': (31-21, 31-21),
                        'IPCSEN': (31-22, 31-22),
                        'TUCSEN': (31-23, 31-23),
                        'PRSDEP': (25-25, 25-24),
                        'Reserved1': (31-26, 31-26),
                        'BC_REJ': (31-27, 31-27),
                        'PROM': (31-28, 31-28),
                        'RSF': (31-29, 31-29),
                        'EMEN': (31-30, 31-30),
                        'Reserved0': (31-31, 31-31)
                    }
                },
                'RDRP': {},
                'RFCS': {},
                'RFLR': {},
                'RFRG': {},
                'RJBR': {},
                'RMCA': {},
                'ROVR': {},
                'RPKT': {},
                'RQFAR': {},
                'RQUEUE': {},
                'RSTAT': {},
                'RSVD': {
                    'count': (6, )
                },
                'RUND': {},
                'RXCF': {},
                'RXPF': {},
                'RXUO': {},
                'TBASE': {
                    'count': (8, )
                },
                'TBASEH': {},
                'TBCA': {},
                'TBDBPH': {},
                'TBIPA': {},
                'TBPTR': {
                    'count': (8, )
                },
                'TBYT': {},
                'TCTRL': {},
                'TDFR': {},
                'TDRP': {},
                'TEDF': {},
                'TFCS': {},
                'TFRG': {},
                'TJBR': {},
                'TLCL': {},
                'TMCA': {},
                'TMCL': {},
                'TNCL': {},
                'TOVR': {},
                'TPKT': {},
                'TQUEUE': {},
                'TR127': {},
                'TR1K': {},
                'TR255': {},
                'TR511': {},
                'TR64': {},
                'TRMAX': {},
                'TRMGV': {},
                'TSCL': {},
                'TSEC_ID': {},
                'TSEC_ID2': {},
                'TSTAT': {},
                'TUND': {},
                'TXCF': {},
                'TXCL': {},
                'TXIC': {},
                'TXPF': {},
                'tbi_ANA': {
                    'bits': 9,
                    'partial': True,
                    'actualBits': 16,
                    'fields': {
                        # Not Implemented
                        # 'Next_Page': (15-0, 15-0),
                        'Reserved2': (15-1, 15-1),
                        # Not Implemented
                        # 'Remote_Fault': (15-3, 15-2),
                        'Reserved1': (15-6, 15-4),
                        # Not Implemented
                        # 'Pause': (15-8, 15-7),
                        # 'Half_Duplex': (15-9, 15-9),
                        # 'Full_Duplex': (15-10, 15-10),
                        'Reserved0': (15-15, 15-11)
                    }
                },
                'tbi_ANEX': {
                    'bits': 16
                },
                'tbi_ANLPANP': {
                    'bits': 16
                },
                'tbi_ANLPBPA': {
                    'bits': 16
                },
                'tbi_ANNPT': {
                    'bits': 2,
                    'partial': True,
                    'actualBits': 16,
                    'fields': {
                        # Not Implemented
                        # 'Next_Page': (15-0, 15-0),
                        'Reserved': (15-1, 15-1),
                        # Not Implemented
                        # 'Msg_Page': (15-2, 15-2),
                        # 'Ack2': (15-3, 15-3),
                        'Toggle': (15-4, 15-4)
                        # Not Implemented
                        # 'Message_Un-formatted_Code_Field': (15-15, 15-5)
                    }
                },
                'tbi_CR': {
                    'bits': 10,
                    'partial': True,
                    'actualBits': 16,
                    'fields': {
                        # Not Implemented
                        # 'PHY_Reset': (15-0, 15-0),
                        'Reserved3': (15-1, 15-1),
                        # Not Implemented
                        # 'Speed_0': (15-2, 15-2),
                        # 'AN_Enable': (15-3, 15-3),
                        'Reserved2': (15-5, 15-4),
                        # Not Implemented
                        # 'Reset_AN': (15-6, 15-6),
                        # 'Full_Duplex': (15-7, 15-7),
                        'Reserved1': (15-8, 15-8),
                        # Not Implemented
                        # 'Speed_1': (15-9, 15-9),
                        'Reserved0': (15-15, 15-10)
                    }
                },
                'tbi_EXST': {
                    'bits': 16
                },
                'tbi_JD': {
                    'bits': 2,
                    'partial': True,
                    'actualBits': 16,
                    'fields': {
                        # Not Implemented
                        # 'Jitter_Enable': (15-0, 15-0),
                        # 'Jitter_Select': (15-3, 15-1),
                        'Reserved': (15-5, 15-4),
                        # Not Implemented
                        # 'Custom_Jitter_Pattern': (15-15, 15-6)
                    }
                },
                'tbi_SR': {
                    'bits': 16
                },
                'tbi_TBICON': {
                    'bits': 10,
                    'partial': True,
                    'actualBits': 16,
                    'fields': {
                        # Not Implemented
                        # 'Soft_Reset': (15-0, 15-0),
                        'Reserved3': (15-1, 15-1),
                        # Not Implemented
                        # 'Disable_Rx_Dis': (15-2, 15-2),
                        # 'Disable_Tx_Dis': (15-3, 15-3),
                        'Reserved2': (15-6, 15-4),
                        # Not Implemented
                        # 'AN_Sense': (15-7, 15-7),
                        'Reserved1': (15-9, 15-8),
                        # Not Implemented
                        # 'Clock_Select': (15-10, 15-10),
                        # 'MI_Mode': (15-11, 15-11),
                        'Reserved0': (15-15, 15-12)
                    }
                }
                # Not Implemented
                # 'FIFOCFG': {},
                # 'FIFO_RX_ALARM': {},
                # 'FIFO_RX_ALARM_SHUTOFF': {},
                # 'FIFO_RX_PAUSE': {},
                # 'FIFO_RX_PAUSE_SHUTOFF': {},
                # 'RFBPTR': {
                #     'count': (8, )
                # },
                # 'RQFCR': {},
                # 'RQFPR': {},
                # 'RQPRM': {
                #     'count': (8, )
                # },
                # 'RREJ': {},
                # 'RXIC': {
                #     'fields': {
                #         # Field ICCS - Coalescing on timer is not yet
                #         #              supported.
                #         # Field ICEN - Not implemented.
                #     }
                # },
                # 'TMR_ACC': {},
                # 'TMR_ADD': {},
                # 'TMR_ALARM1_H': {},
                # 'TMR_ALARM1_L': {},
                # 'TMR_ALARM2_H': {},
                # 'TMR_ALARM2_L': {},
                # 'TMR_CNT_H': {},
                # 'TMR_CNT_L': {},
                # 'TMR_CTRL': {},
                # 'TMR_ETTS1_H': {},
                # 'TMR_ETTS1_L': {},
                # 'TMR_ETTS2_H': {},
                # 'TMR_ETTS2_L': {},
                # 'TMR_FIPER1': {},
                # 'TMR_FIPER2': {},
                # 'TMR_FIPER3': {},
                # 'TMR_OFF_H': {},
                # 'TMR_OFF_L': {},
                # 'TMR_PEMASK': {},
                # 'TMR_PEVENT': {},
                # 'TMR_PRSC': {},
                # 'TMR_RXTS_H': {},
                # 'TMR_RXTS_L': {},
                # 'TMR_STAT': {},
                # 'TMR_TEMASK': {},
                # 'TMR_TEVENT': {},
                # 'TMR_TXTS1_H': {},
                # 'TMR_TXTS1_ID': {},
                # 'TMR_TXTS1_L': {},
                # 'TMR_TXTS2_H': {},
                # 'TMR_TXTS2_ID': {},
                # 'TMR_TXTS2_L': {},
                # 'TR03WT': {},
                # 'TR47WT': {}
            }
        },
        'GPIO': {
            'OBJECT': '.soc.gpio',
            'TYPE': 'qoriq-p2-gpio',
            'registers': {
                'GPDAT': {},
                'GPDIR': {},
                'GPICR': {},
                'GPIER': {},
                'GPIMR': {},
                'GPODR': {}
            }
        },
        'GU': {
            'OBJECT': '.soc.gu',
            'TYPE': 'qoriq-p2-gu',
            'registers': {
                'AUTORSTSR': {},
                'CLKOCR': {},
                'GPPORCR': {},
                'MCPSUMR': {},
                'PMUXCR': {},
                'PORBMSR': {},
                'PORDBGMSR': {},
                'PORDEVSR': {},
                'PORPLLSR': {},
                'POWMGTCSR': {},
                'PVR': {},
                'RSTCR': {},
                'SVR': {}
                # Not Implemented
                # 'DDRCLKDR': {},
                # 'DEVDISR': {},
                # 'ECMCR': {},
                # 'ECTRSTCR': {},
                # 'IOVSELCR': {},
                # 'PMCDR': {},
                # 'PORDEVSR2': {},
                # 'RSTRSCR': {},
                # 'SRDSCR': {
                #     'count': 2
                # }
            }
        },
        'I2C': {
            # LIMITATIONS: Slave mode not supported
            #              Arbitration lost not supported/detectable
            'count': 2,
            'OBJECT': '.soc.i2c',
            'TYPE': 'qoriq-p2-i2c',
            'registers': {
                'I2CCR': {},
                'I2CDFSRR': {},
                'I2CSR': {},
                'I2CFDR': {},
                'I2CDR': {},
                'I2CADR': {}
            }
        },
        'L2SRAM': {
            'OBJECT': '.soc.l2sram',
            'TYPE': 'qoriq-p2-l2',
            'registers': {
                'L2CTL': {
                    'fields': {
                        'L2E': (31-0, 31-0),
                        'L2I': (31-1, 31-1),
                        'L2SIZ': (31-3, 31-2),
                        'Reserved5': (31-8, 31-4),
                        'L2DO': (31-9, 31-9),        # Write-access not
                                                     # implemented
                        'L2IO': (31-10, 31-10),      # Write-access not
                                                     # implemented
                        'Reserved4': (31-11, 31-11),
                        'L2INTDIS': (31-12, 31-12),  # Write-access not
                                                     # implemented
                        'L2SRAM': (31-15, 31-13),
                        'Reserved3': (31-17, 31-16),
                        'L2LO': (31-18, 31-18),      # Write-access not
                                                     # implemented
                        'L2LSC': (31-19, 31-19),     # Write-access not
                                                     # implemented
                        'Reserved2': (31-20, 31-20),
                        'L2LFR': (31-21, 31-21),
                        'L2LFRID': (31-23, 31-22),   # Write-access not
                                                     # implemented
                        'Reserved1': (31-27, 31-24),
                        'L2STASHDIS': (31-28, 31-28),
                        'Reserverd0': (31-29, 31-29),
                        'L2STASHCTL': (31-31, 31-30)
                    }
                },
                'L2SRBAREA': {
                    'count': (2, )
                },
                'L2SRBAR': {
                    'count': (2, )
                }
                # Not Implemented
                # 'L2CAPTDATAHI': {},
                # 'L2CAPTDATALO': {},
                # 'L2CAPTECC': {},
                # 'L2CEWAREA': {
                #     'count': (4, )
                # },
                # 'L2CEWAR': {
                #     'count': (4, )
                # },
                # 'L2CEWCR': {
                #     'count': (4, )
                # },
                # 'L2ERRADDR': {},
                # 'L2ERRATTR': {},
                # 'L2ERRCTL': {},
                # 'L2ERRDET': {},
                # 'L2ERRDIS': {},
                # 'L2ERRINJCTL': {},
                # 'L2ERRINJHI': {},
                # 'L2ERRINJLO': {},
                # 'L2ERRINTEN': {}
            }
        },
        'MC': {
            'OBJECT': '.soc.mc',
            'TYPE': 'qoriq-p2-ddr-mc',
            'registers': {
                'CAPTURE_ADDRESS': {},
                'CAPTURE_ATTRIBUTES': {},
                'CAPTURE_DATA_HI': {},
                'CAPTURE_DATA_LO': {},
                'CAPTURE_ECC': {},
                'CS_BNDS': {
                    'count': (4, ),
                    'fields': {
                        'Reserved1': (31-3, 31-0),
                        'SAn': (31-15, 31-4),
                        'Reserved0': (31-19, 31-16),
                        'EAn': (31-31, 31-20)
                    }
                },
                'CS_CONFIG': {
                    'count': (4, ),
                    'fields': {
                        'CS_EN': (31-0, 31-0),
                        'Reserved3': (31-7, 31-1),
                        'AP_EN': (31-8, 31-8),
                        'ODT_RD_CFG': (31-11, 31-9),
                        'Reserved2': (31-12, 31-12),
                        'ODT_WR_CFG': (31-15, 31-13),
                        'BA_BITS_CS': (31-17, 31-16),
                        'Reserved1': (31-20, 31-18),
                        'ROW_BITS_CS': (31-23, 31-21),
                        'Reserved0': (31-28, 31-24),
                        'COL_BITS_CS': (31-31, 31-29)
                    }
                },
                'CS_CONFIG_2': {
                    'count': (4, ),
                    'fields': {
                        'Reserved1': (31-4, 31-0),
                        'PASR_CFG': (31-7, 31-5),
                        'Reserved0': (31-31, 31-8)
                    }
                },
                'DATA_ERR_INJECT_HI': {},
                'DATA_ERR_INJECT_LO': {},
                'DDR_IP_REV1': {},
                'DDR_IP_REV2': {},
                'DDR_SDRAM_CFG': {
                    'bits': 31,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'MEM_EN': (31-0, 31-0),
                        'SREN': (31-1, 31-1),
                        'ECC_EN': (31-2, 31-2),
                        'RD_EN': (31-3, 31-3),
                        'Reserved4': (31-4, 31-4),
                        'SDRAM_TYPE': (31-7, 31-5),
                        'Reserved3': (31-9, 31-8),
                        'DYN_PWR': (31-10, 31-10),
                        'DBW': (31-12, 31-11),
                        '8_BE': (31-13, 31-13),
                        'Reserved2': (31-14, 31-14),
                        '3T_EN': (31-15, 31-15),
                        '2T_EN': (31-16, 31-16),
                        'BA_INTLV_CTL': (31-23, 31-17),
                        'Reserved1': (31-25, 31-24),
                        'x32_EN': (31-26, 31-26),
                        'PCHB8': (31-27, 31-27),
                        'HSE': (31-28, 31-28),
                        'Reserved0': (31-29, 31-29),
                        'MEM_HALT': (31-30, 31-30)
                        # Not Implemented
                        # 'BI': (31-31, 31-31)
                    },
                },
                'DDR_SDRAM_CFG_2': {
                    'bits': 31,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'FRC_SR': (31-0, 31-0),
                        'SR_IE': (31-1, 31-1),
                        'DLL_RST_DIS': (31-2, 31-2),
                        'Reserved5': (31-3, 31-3),
                        'DQS_CFG': (31-5, 31-4),
                        'Reserved4': (31-8, 31-6),
                        'ODT_CFG': (31-10, 31-9),
                        'Reserved3': (31-15, 31-11),
                        'NUM_PR': (31-19, 31-16),
                        'Reserved2': (31-24, 31-20),
                        'OBC_CFG': (31-25, 31-25),
                        'AP_EN': (31-26, 31-26),
                        # Not Implemented
                        # 'D_INIT': (31-27, 31-27),
                        'Reserved1': (31-28, 31-28),
                        'RCW_EN': (31-29, 31-29),
                        'Reserved0': (31-30, 31-30),
                        'MD_EN': (31-31, 31-31)
                    },
                },
                'DDR_SDRAM_CLK_CNTRL': {},
                'DDR_SDRAM_INTERVAL': {},
                'DDR_SDRAM_MD_CNTL': {},
                'DDR_SDRAM_MODE': {},
                'DDR_SDRAM_MODE_2': {},
                'DDR_SR_CNTR': {},
                'DDR_WRLVL_CNTL': {},
                'DDR_WRLVL_CNTL_2': {},
                'DDR_WRLVL_CNTL_3': {},
                'DDR_ZQ_CNTL': {},
                'ERR_DETECT': {},
                'ERR_DISABLE': {},
                'ERR_INT_EN': {},
                'ERR_SBE': {},
                'TIMING_CFG_0': {},
                'TIMING_CFG_1': {},
                'TIMING_CFG_2': {},
                'TIMING_CFG_3': {},
                'TIMING_CFG_4': {},
                'TIMING_CFG_5': {}
                # Not Implemented
                # 'CAPTURE_EXT_ADDRESS': {},
                # 'DDRCDR_1': {},
                # 'DDRCDR_2': {},
                # 'DDRDSR_1': {},
                # 'DDRDSR_2': {},
                # 'DDR_INIT_ADDRESS': {},
                # 'DDR_INIT_EXT_ADDRESS': {},
                # 'DDR_SDRAM_INIT': {},
                # 'DDR_SDRAM_RCW': {}
            }
        },
        'PCIE': {
            # LIMITATIONS: PCI capabilities (i.e. the standard PCI capabilities
            #              defined in a linked list in PCI configuration space)
            #              are typically only dummy registers, as PCI
            #              capabilities are usually too low-level for Simics.
            #              Error management registers only have dummy
            #              implementation.
            'count': 3,
            'OBJECT': '.soc.pcie_bridge',
            'TYPE': 'qoriq-p2-pcie',
            'registers': {
                'PEX_CONFIG': {
                    'bits': 29,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved1': (31-26, 31-0),
                        # Not Implemented
                        # 'SAC': (31-27, 31-27),
                        'Reserved0': (31-29, 31-28),
                        # Not Implemented
                        # 'SP': (31-30, 31-30),
                        # 'SCC': (31-31, 31-31)
                    }
                },
                'PEX_CONFIG_ADDR': {},
                'PEX_CONFIG_RTY_TOR': {},  # Timeout will never occur
                'PEX_IP_BLK_REV1': {},
                'PEX_IP_BLK_REV2': {},
                'PEX_OTB_CPL_TOR': {},     # Timeout will never occur
                'PEX_PME_MES_DISR': {},
                'PEX_PME_MES_DR': {},
                'PEX_PME_MES_IER': {},
                'PEX_inbound_ITAR': {
                    'count': (3, )
                },
                'PEX_inbound_IWAR': {
                    'count': (3, ),
                    'fields': {
                        'EN': (31-0, 31-0),
                        'Reserved2': (31-1, 31-1),
                        'PF': (31-2, 31-2),        # Not forced to 0 when
                                                   # TRGT = CCSRBAR
                        'Reserved1': (31-7, 31-3),
                        'TRGT': (31-11, 31-8),
                        'RTT': (31-15, 31-12),     # Only read transaction type
                                                   # implemented (0x4)
                        'WTT': (31-19, 31-16),     # Only write transaction type
                                                   # implemented (0x4)
                        'Reserved0': (31-25, 31-20),
                        'IWS': (31-31, 31-26)
                    }
                },
                'PEX_inbound_IWBAR': {
                    'count': (3, )
                },
                'PEX_inbound_IWBEAR': {
                    'count': (3, )
                },
                'PEX_outbound_OTAR': {
                    'count': (5, )
                },
                'PEX_outbound_OTEAR': {
                    'count': (5, )
                },
                'PEX_outbound_OTWBAR': {
                    'count': (5, )
                },
                'PEX_outbound_OWAR': {
                    'count': (5, ),
                    'bits': 27,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'EN': (31-0, 31-0),
                        'Reserved3': (31-2, 31-1),
                        # Not Implemented
                        # 'ROE': (31-3, 31-3),
                        # 'NS': (31-4, 31-4),
                        'Reserved2': (31-7, 31-5),
                        # Not Implemented
                        # 'TC': (31-10, 31-8),
                        'Reserved1': (31-11, 31-11),
                        'RTT': (31-15, 31-12),
                        'WTT': (31-19, 31-16),
                        'Reserved0': (31-25, 31-20),
                        'OWS': (31-31, 31-26)
                    }
                }
                # Not found in P2020 Docs
                # 'command': {
                #     'fields': {
                #         Field fb - Not implemented.
                #         Field mwi - Not implemented.
                #         Field pe - Not implemented.
                #         Field sc - Not implemented.
                #         Field se - Not implemented.
                #         Field vga - Not implemented.
                #         Field wc - Not implemented.
                #     }
                # }
                # Not Implemented
                # 'PEX_ERR_CAP_R': {
                #     'count': (4, )
                # },
                # 'PEX_ERR_CAP_STAT': {},
                # 'PEX_ERR_DISR': {},
                # 'PEX_ERR_DR': {},
                # 'PEX_ERR_EN': {},
                # 'PEX_LTSSM_STAT': {},
                # 'PEX_PDB_STAT': {},
            }
        },
        'PIC': {
            # LIMITATIONS: The priority between interrupts with the same
            #              xVPR[PRIORITY] values are not guaranteed.
            #              Edge triggered interrupts are not supported.
            'OBJECT': '.soc.pic',
            'TYPE': 'qoriq-p2-pic',
            'registers': {
                'BRR1': {},
                'BRR2': {},
                'EIDR': {
                    'count': (12, )
                },
                'EIVPR': {
                    'count': (12, )
                },
                'FRR': {},
                'GCR': {},
                'GT_GTBCR': {
                    'count': (2, 4)
                },
                'GT_GTCCR': {
                    'count': (2, 4)
                },
                'GT_GTDR': {
                    'count': (2, 4)
                },
                'GT_GTVPR': {
                    'count': (2, 4)
                },
                'GT_TCR': {
                    'count': (2, )
                },
                'GT_TFRR': {
                    'count': (2, )
                },
                'IIDR': {
                    'count': (64, )
                },
                'IIVPR': {
                    'count': (64, )
                },
                'IPIVPR': {
                    'count': (4, )
                },
                'MSG_MER': {
                    'count': (2, )
                },
                'MSG_MIDR': {
                    'count': (2, 4)
                },
                'MSG_MIVPR': {
                    'count': (2, 4)
                },
                'MSG_MSGR': {
                    'count': (2, 4)
                },
                'MSI_MSIDR': {
                    'count': (1, 8)
                },
                'MSI_MSIR': {
                    'count': (1, 8)
                },
                'MSI_MSISR': {
                    'count': (1, )
                },
                'MSI_MSIVPR': {
                    'count': (1, 8)
                },
                'PIR': {},
                'PM_MR': {
                    'count': (4, 3)
                },
                'P_CTPR': {
                    'count': (8, )  # only 3 in P2020 docs
                },
                'P_IPIDR': {
                    'count': (8, 4)  # only 3 in P2020 docs
                },
                'SVR': {},
                'VIR': {}
                # Not Implemented
                # 'CISR': {
                #     'count': (3, )
                # },
                # 'ERQSR': {},
                # 'IRQSR': {
                #     'count': (3, )
                # },
                # 'MSG_MSR': {
                #     'count': (2, )
                # }
            }
        },
        'RAPIDIO': {
            # Limitations:
            # These parts of the RapidIO controller are implemented:
            #       Maintenance operations: read/write of configuration
            #                               registers.
            #       Outgoing doorbell messages.
            #       Outgoing memory operations.
            #       Outgoing messages from both mailboxes.
            #       Incoming doorbell messages.
            #       Incoming messages into both mailboxes.
            #       Incoming memory operations.
            # These parts are not implemented:
            #       Operations crossing outbound window borders.
            #       Operations crossing inbound window borders.
            #       Incoming packet filtering based on target ID.
            'OBJECT': '.soc.rapidio',
            'TYPE': 'qoriq-p2-rapidio',
            'registers': {
                'regs_DMIRIR': {},
                'regs_DMR': {},
                'regs_DQDPAR': {},
                'regs_DQEPAR': {},
                'regs_DSR': {},
                'regs_EDQDPAR': {},
                'regs_EDQEPAR': {},
                'regs_EPWISR': {},
                'regs_EPWQBAR': {},
                'regs_IPBRR1': {},
                'regs_IPBRR2': {},
                'regs_LLCR': {},
                'regs_LRETCR': {},
                'regs_M_EIFQDPAR': {
                    'count': (2, )
                },
                'regs_M_EIFQEPAR': {
                    'count': (2, )
                },
                'regs_M_EODQDPAR': {
                    'count': (2, )
                },
                'regs_M_EODQEPAR': {
                    'count': (2, )
                },
                'regs_M_EOSAR': {
                    'count': (2, )
                },
                'regs_M_IFQDPAR': {
                    'count': (2, )
                },
                'regs_M_IFQEPAR': {
                    'count': (2, )
                },
                'regs_M_IMIRIR': {
                    'count': (2, )
                },
                'regs_M_IMR': {
                    'count': (2, )
                },
                'regs_M_ISR': {
                    'count': (2, )
                },
                'regs_M_ODATR': {
                    'count': (2, )
                },
                'regs_M_ODCR': {
                    'count': (2, )
                },
                'regs_M_ODPR': {
                    'count': (2, )
                },
                'regs_M_ODQDPAR': {
                    'count': (2, )
                },
                'regs_M_ODQEPAR': {
                    'count': (2, )
                },
                'regs_M_OMGR': {
                    'count': (2, )
                },
                'regs_M_OMLR': {
                    'count': (2, )
                },
                'regs_M_OMR': {
                    'count': (2, )
                },
                'regs_M_ORETCR': {
                    'count': (2, )
                },
                'regs_M_OSAR': {
                    'count': (2, )
                },
                'regs_M_OSR': {
                    'count': (2, )
                },
                'regs_ODDATR': {},
                'regs_ODDPR': {},
                'regs_ODMR': {},
                'regs_ODRETCR': {},
                'regs_ODRS': {},
                'regs_PRTOCCSR': {},
                'regs_PWMR': {},
                'regs_PWQBAR': {},
                'regs_PWSR': {},
                'regs_assembly_id': {},
                'regs_assembly_info': {},
                'regs_base1_status': {},
                'regs_base1_status_hi': {},
                'regs_base_device_id': {},
                'regs_component_tag': {},
                'regs_conf_dest_id': {},
                'regs_conf_output_port': {},
                'regs_default_output_port': {},
                'regs_device_id': {},
                'regs_device_info': {},
                'regs_dst_operations': {},
                'regs_error_block_header': {},
                'regs_host_base_device_id': {},
                'regs_layer_error_detect': {},
                'regs_layer_error_enable': {},
                'regs_packet_ttl': {},
                'regs_pe_features': {},
                'regs_pe_ll_status': {},
                'regs_port_AACR': {
                    'count': (2, )
                },
                'regs_port_LOPTTLCR': {
                    'count': (2, )
                },
                'regs_port_RIWAR0': {
                    'count': (2, )
                },
                'regs_port_RIWARn': {
                    'count': (2, 4)
                },
                'regs_port_RIWBARn': {
                    'count': (2, 4)
                },
                'regs_port_RIWTAR0': {
                    'count': (2, )
                },
                'regs_port_RIWTARn': {
                    'count': (2, 4)
                },
                'regs_port_ROWAR0': {
                    'count': (2, )
                },
                'regs_port_ROWARn': {
                    'count': (2, 8)
                },
                'regs_port_ROWBARn': {
                    'count': (2, 8)
                },
                'regs_port_ROWS1R': {
                    'count': (2, 8)
                },
                'regs_port_ROWS2R': {
                    'count': (2, 8)
                },
                'regs_port_ROWS3R': {
                    'count': (2, 8)
                },
                'regs_port_ROWTAR0': {
                    'count': (2, )
                },
                'regs_port_ROWTARn': {
                    'count': (2, 8)
                },
                'regs_port_ROWTEAR': {
                    'count': (2, 8)
                },
                'regs_port_ROWTEAR0': {
                    'count': (2, )
                },
                'regs_port_SLCSR': {
                    'count': (2, )
                },
                'regs_port_block_header': {},
                'regs_port_general_control': {},
                'regs_port_link_timeout': {},
                'regs_port_port_control': {
                    'count': (2, ),
                    'bits': 28,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'PW': (31-1, 31-0),
                        'IPW': (31-4, 31-2),
                        'PWO': (31-7, 31-5),
                        # Not Implemented
                        # 'PD': (31-8, 31-8),
                        # 'OPE': (31-9, 31-9),
                        # 'IPE': (31-10, 31-10),
                        'ECD': (31-11, 31-11),
                        'MEP': (31-12, 31-12),
                        'Reserved': (31-27, 31-13),
                        'SPF': (31-28, 31-28),
                        'DPE': (31-29, 31-29),
                        # Not Implemented
                        # 'PL': (31-30, 31-30),
                        'PT': (31-31, 31-31)
                    }
                },
                'regs_port_port_error_and_status': {
                    'count': (2, )
                },
                'regs_portwrite_target_id': {},
                'regs_src_operations': {},
                'regs_switch_info': {},
                'regs_write_port_status': {}
                # Not Implemented
                # 'regs_PRETCR': {},
                # 'regs_layer_capture_address': {},
                # 'regs_layer_capture_address_hi': {},
                # 'regs_layer_capture_control': {},
                # 'regs_layer_capture_device_id': {},
                # 'regs_port_ADIDCSR': {
                #     'count': (2, )
                # },
                # 'regs_port_IECSR': {
                #     'count': (2, )
                # },
                # 'regs_port_PCR': {
                #     'count': (2, )
                # },
                # 'regs_port_SLEICR': {
                #     'count': (2, )
                # },
                # 'regs_port_link_maintenance_request': {
                #     'count': (2, )
                # },
                # 'regs_port_link_maintenance_response': {
                #     'count': (2, )
                # },
                # 'regs_port_capture_attributes': {
                #     'count': (2, )
                # },
                # 'regs_port_capture_packet_1': {
                #     'count': (2, )
                # },
                # 'regs_port_capture_packet_2': {
                #     'count': (2, )
                # },
                # 'regs_port_capture_packet_3': {
                #     'count': (2, )
                # },
                # 'regs_port_capture_symbol': {
                #     'count': (2, )
                # },
                # 'regs_port_port_error_detect': {
                #     'count': (2, )
                # },
                # 'regs_port_port_error_rate': {
                #     'count': (2, )
                # },
                # 'regs_port_port_error_rate_enable': {
                #     'count': (2, )
                # },
                # 'regs_port_port_error_rate_threshold': {
                #     'count': (2, )
                # },
                # 'regs_port_port_local_ackid_status': {
                #     'count': (2, )
                # }
            }
        },
        'USB': {
            # LIMITATIONS: Device mode not implemented.
            #              Interrupt and Isochronous transfers not supported
            #              Cannot handle when USB devices send NAK or STALL
            #              status during Control and Bulk transfers
            #              Cannot handle USB devices with a latency
            #              (submit_transfer must return USB_Transfer_ Completed)
            #              Bulk and Control transfers will only be initiated
            #              while the attribute async_list_polling_enabled
            #              is set.
            #              Asynchronous schedule park capability not
            #              implemented.
            #              Extensions to EHCI not implemented.
            'OBJECT': '.soc.usb',
            'TYPE': 'qoriq-p2-usb',
            'registers': {
                'regs_BURSTSIZE': {},  # Write-access not implemented
                'regs_DCCPARAMS': {},
                'regs_DCIVERSION': {
                    'bits': 16
                },
                'regs_DEVICEADDR': {},
                'regs_ENDPOINTLISTADDR': {},
                'regs_USBMODE': {
                    'bits': 30,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved1': (5, 31),
                        # 'SDIS': (4, 4),
                        # 'SLOM': (3, 3),
                        'Reserved0': (2, 2),
                        'CM': (0, 1)
                    }
                },
                'usb_regs_caplength': {
                    'bits': 8
                },
                'usb_regs_configflag': {},
                'usb_regs_ctrldssegment': {},
                'usb_regs_frindex': {},  # The controller may process frames
                                         # in advance
                'usb_regs_hccparams': {},
                'usb_regs_hciversion': {
                    'bits': 16,
                },
                'usb_regs_hcsp_portroute': {},
                'usb_regs_hcsparams': {},
                'usb_regs_periodiclistbase': {},
                'usb_regs_prtsc': {
                    'count': (1, ),
                    'bits': 26,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        # Not Implemented
                        # 'PTS': (30, 31),
                        'Reserved2': (28, 29),
                        'PSPD': (26, 27),
                        'Reserved1': (25, 25),
                        # Not Implemented
                        # 'PFSC': (24, 24),
                        'PHCD': (23, 23),
                        # Not Implemented
                        # 'WKOC': (22, 22),
                        # 'WKDS': (21, 21),
                        # 'WKCN': (20, 20),
                        'PTC': (16, 19),     # Write-access not implemented
                        'PIC': (14, 15),
                        'PO': (13, 13),
                        'PP': (12, 12),
                        'LS': (10, 11),
                        'Reserved0': (9, 9),
                        'PR': (8, 8),
                        'SUSP': (7, 7),      # Write-access not implemented
                        'FPR': (6, 6),       # Write-access not implemented
                        'OCC': (5, 5),       # Read-access not implemented
                        'OCA': (4, 4),       # Read-access not implemented
                        'PEC': (3, 3),
                        'PE': (2, 2),
                        'CSC': (1, 1),
                        'CCS': (0, 0)
                    }
                },
                'usb_regs_reserved': {},
                'usb_regs_usbcmd': {
                    'bits': 21,
                    'partial': True,
                    'actualBits': 32,
                    'fields': {
                        'Reserved2': (24, 31),
                        # Not Implemented
                        # 'ITC': (16, 23),
                        'FS2': (15, 15),      # Write-access not implemented
                        'ATDTW': (14, 14),    # Write-access not implemented
                        'SUTW': (13, 13),     # Write-access not implemented
                        'Reserved1': (12, 12),
                        # Not Implemented
                        # 'ASPE': (11, 11),
                        'Reserved0': (10, 10),
                        # Not Implemented
                        # 'ASP': (8, 9),
                        'LR': (7, 7),         # Write-access not implemented
                        'IAA': (6, 6),
                        'ASE': (5, 5),
                        'PSE': (4, 4),
                        'FS': (2, 3),
                        'RST': (1, 1),
                        'RS': (0, 0)
                    }
                },
                'usb_regs_usbintr': {
                    'fields': {
                        'Reserved1': (11, 31),
                        'ULPIE': (10, 10),    # Write-access not implemented
                        'Reserved0': (9, 9),
                        'SLE': (8, 8),        # Write-access not implemented
                        'SRE': (7, 7),        # Write-access not implemented
                        'URE': (6, 6),        # Write-access not implemented
                        'AAE': (5, 5),
                        'SEE': (4, 4),
                        'FRE': (3, 3),
                        'PCE': (2, 2),
                        'UEE': (1, 1),
                        'UE': (0, 0)
                    }
                },
                'usb_regs_usbsts': {
                    'fields': {
                        'Reserved2': (16, 31),
                        'AS': (15, 15),        # Read-access not implemented
                        'PS': (14, 14),
                        'RCL': (13, 13),       # Read-access not implemented
                        'HCH': (12, 12),
                        'Reserved1': (11, 11),
                        'ULPII': (10, 10),     # Write-access not implemented
                        'Resevrved0': (9, 9),
                        'SLI': (8, 8),         # Write-access not implemented
                        'SRI': (7, 7),         # Write-access not implemented
                        'URI': (6, 6),         # Write-access not implemented
                        'AAI': (5, 5),
                        'SEI': (4, 4),
                        'FRI': (3, 3),
                        'PCI': (2, 2),
                        'UEI': (1, 1),
                        'UI': (0, 0)
                    }
                }
                # Not Implemented
                # 'regs_AGE_CNT_THRESH': {},
                # 'regs_CONTROL': {},
                # 'regs_ENDPOINTPRIME': {},
                # 'regs_ENDPTCOMPLETE': {},
                # 'regs_ENDPTCTRL': {
                #     'count': (3, )
                # },
                # 'regs_ENDPTFLUSH': {},
                # 'regs_ENDPTSETUPSTAT': {},
                # 'regs_ENDPTSTATUS': {},
                # 'regs_PRI_CTRL': {},
                # 'regs_SI_CTRL': {},
                # 'regs_SNOOP': {
                #     'count': (2, )
                # },
                # 'regs_TXFILLTUNING': {},
                # 'regs_ULPI_VIEWPORT': {}
            }
        }
    }
}

for device in devices:
    for target in devices[device]:
        # count bits for each target
        total_bits = 0
        for register in devices[device][target]['registers']:
            if 'bits' in devices[device][target]['registers'][register]:
                bits = devices[device][target]['registers'][register]['bits']
            else:
                bits = 32
            if 'count' in devices[device][target]['registers'][register]:
                count = 1
                for dimension in (devices[device][target]['registers']
                                         [register]['count']):
                    count *= dimension
            else:
                count = 1
            (devices[device][target]['registers']
                    [register]['total_bits']) = count * bits
            total_bits += count * bits
            # if a register is partially implemented generate an adjust_bit
            # mapping list to ensure an unimplemented field is not injected into
            if ('partial' in devices[device][target]['registers'][register] and
                    devices[device][target]['registers'][register]['partial']):
                adjust_bit = []
                for field, field_range in (devices[device][target]
                                                  ['registers'][register]
                                                  ['fields'].iteritems()):
                    for bit in xrange(field_range[0], field_range[1]+1):
                        adjust_bit.append(bit)
                if len(adjust_bit) != bits:
                    raise Exception('simics_targets.py: ' +
                                    'bits mismatch for register: '+register +
                                    ' in target: '+target)
                else:
                    (devices[device][target]['registers'][register]
                            ['adjust_bit']) = sorted(adjust_bit)
        devices[device][target]['total_bits'] = total_bits

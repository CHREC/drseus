from targets import calculate_target_bits

targets = {
    'CPU': {
        'count': 2,
        'OBJECT': 'coretile.mpcore.core',
        'registers': {
            'cpsr': {},
            'lr_abt': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (4, 14)
                }
            },
            'lr_fiq': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (1, 14)
                }
            },
            'lr_irq': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (2, 14)
                }
            },
            'lr_mon': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (0, 14)
                }
            },
            'lr_svc': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (5, 14)
                }
            },
            'lr_und': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (3, 14)
                }
            },
            'lr_usr': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 14)
                }
            },
            'pc': {
                'bits': 31,
                'partial': True,
                'actual_bits': 32,
                'fields': {
                    'addr': (1, 31)  # Cannot write unaligned pc
                },
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 15)
                }
            },
            'sp_abt': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (4, 13)
                }
            },
            'sp_fiq': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (1, 13)
                }
            },
            'sp_irq': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (2, 13)
                }
            },
            'sp_mon': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (0, 13)
                }
            },
            'sp_svc': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (5, 13)
                }
            },
            'sp_und': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (3, 13)
                }
            },
            'sp_usr': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 13)
                }
            },
            # 'spsr': {  # mod, fiq, irq, und, abt, svc, usr
            #     'count': (7, )
            # },
            'spsr_abt': {
                'alias': {
                    'register': 'spsr',
                    'register_index': (4, )
                }
            },
            'spsr_fiq': {
                'alias': {
                    'register': 'spsr',
                    'register_index': (1, )
                }
            },
            'spsr_irq': {
                'alias': {
                    'register': 'spsr',
                    'register_index': (2, )
                }
            },
            'spsr_mon': {
                'alias': {
                    'register': 'spsr',
                    'register_index': (0, )
                }
            },
            'spsr_svc': {
                'alias': {
                    'register': 'spsr',
                    'register_index': (5, )
                }
            },
            'spsr_und': {
                'alias': {
                    'register': 'spsr',
                    'register_index': (3, )
                }
            },
            'spsr_usr': {
                'alias': {
                    'register': 'spsr',
                    'register_index': (6, )
                }
            }
        }
    },
    'FPGPR': {
        'count': 2,
        'OBJECT': 'coretile.mpcore.core',
        'registers': {
            'fpgprs': {
                'bits': 64,
                'count': (32, )
            }
        }
    },
    'GPR': {
        'count': 2,
        'OBJECT': 'coretile.mpcore.core',
        'registers': {
            # 'gprs': {  # mod, fiq, irq, und, abt, svc, usr
            #     'count': (7, 16),
            # },
            'r0': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 0)
                }
            },
            'r1': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 1)
                }
            },
            'r2': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 2)
                }
            },
            'r3': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 3)
                }
            },
            'r4': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 4)
                }
            },
            'r5': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 5)
                }
            },
            'r6': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 6)
                }
            },
            'r7': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 7)
                }
            },
            'r8': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 8)
                }
            },
            'r9': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 9)
                }
            },
            'r10': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 10)
                }
            },
            'r11': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 11)
                }
            },
            'r12': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (6, 12)
                }
            },
            'r8_fiq': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (1, 8)
                }
            },
            'r9_fiq': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (1, 9)
                }
            },
            'r10_fiq': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (1, 10)
                }
            },
            'r11_fiq': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (1, 11)
                }
            },
            'r12_fiq': {
                'alias': {
                    'register': 'gprs',
                    'register_index': (1, 12)
                }
            }
        }
    },
    # 'TLB': {
    #     'count': 2,
    #     'OBJECT': 'coretile.mpcore.core',
    #     'registers': {
    #         'tlb': {
    #             'count': (4, 7, 6),
    #         },
    #     },
    # }
}

calculate_target_bits(targets)

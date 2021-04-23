# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from ...peripheral_models.interrupts import Interrupts
from ...peripheral_models.canbus import CanBus
from avatar2.peripherals.avatar_peripheral import AvatarPeripheral
from ..intercepts import tx_map, rx_map
from ..bp_handler import BPHandler, bp_handler
import time
from collections import defaultdict

import queue
import logging

log = logging.getLogger("STM32F4_CAN")
log.setLevel(logging.INFO)


class STM32_CAN(BPHandler):


    def __init__(self, model=CanBus):
        self.model = model
        self.name = 'CanBus'

    @bp_handler(['HAL_CAN_MspInit', 'HAL_CAN_Init', 'HAL_CAN_Start'])
    def handle_init(self, qemu, bp_addr):
        handle_obj = qemu.regs.r0
        handle_base = qemu.read_memory(handle_obj, 4, 1)

        log.info("STM32_CAN Init, base: %#08x" % (handle_base))
        
        # Nop This function by returning
        return True, None

    @bp_handler(['HAL_CAN_MspDeInit'])
    def handle_deinit(self, qemu, bp_addr):
        handle_obj = qemu.regs.r0
        handle_base = qemu.read_memory(handle_obj, 4, 1)

        log.info("STM32_CAN DeInit, base: %#08x" % (handle_base))
        
        # Nop This function by returning
        return True, None

    # HAL_StatusTypeDef HAL_CAN_AddTxMessage(CAN_HandleTypeDef *hcan, 
    #     CAN_TxHeaderTypeDef *pHeader, 
    #     uint8_t aData[], 
    #     uint32_t *pTxMailbox);
    @bp_handler(['HAL_CAN_AddTxMessage'])
    def handle_tx(self, qemu, bp_addr):
        """
        This function captures messages sent on the CANBus by the firmware.
        """
        # For the moment, do nothing.
        return False, 0

    # HAL_StatusTypeDef HAL_CAN_GetRxMessage(CAN_HandleTypeDef *hcan, 
    #     uint32_t RxFifo, 
    #     CAN_RxHeaderTypeDef *pHeader, 
    #     uint8_t aData[]);
    @bp_handler(['HAL_CAN_GetRxMessage'])
    def handle_rx(self, qemu, bp_addr):
        can_id_ptr = qemu.regs.r0
        can_rxfifo = qemu.regs.r1
        can_rxheader_ptr = qemu.regs.r2
        can_data_ptr = qemu.regs.r3

        # can message from PS
        canmsg = self.model.rx_queue[0].popleft() # FIFO, popleft pops FI.
        can_data = canmsg.get("data", None)
        can_extid = canmsg.get("extid", 0)

        if len(can_data) != 8:
            raise Exception("Can DATA is not a valid length")

        # write_memory(self, address, wordsize, val, num_words=1, raw=False)
        qemu.write_memory(can_data_ptr, 1, can_data, 8)

        """
        TODO: set up CAN Header Data?
        NOTE: of these headers we know at least ExtID is needed.

        /* Get the header */
        pHeader->IDE = CAN_RI0R_IDE & hcan->Instance->sFIFOMailBox[RxFifo].RIR;
        if (pHeader->IDE == CAN_ID_STD)
        {
          pHeader->StdId = (CAN_RI0R_STID & hcan->Instance->sFIFOMailBox[RxFifo].RIR) >> CAN_TI0R_STID_Pos;
        }
        else
        {
          pHeader->ExtId = ((CAN_RI0R_EXID | CAN_RI0R_STID) & hcan->Instance->sFIFOMailBox[RxFifo].RIR) >> CAN_RI0R_EXID_Pos;
        }
        pHeader->RTR = (CAN_RI0R_RTR & hcan->Instance->sFIFOMailBox[RxFifo].RIR);
        pHeader->DLC = (CAN_RDT0R_DLC & hcan->Instance->sFIFOMailBox[RxFifo].RDTR) >> CAN_RDT0R_DLC_Pos;
        pHeader->FilterMatchIndex = (CAN_RDT0R_FMI & hcan->Instance->sFIFOMailBox[RxFifo].RDTR) >> CAN_RDT0R_FMI_Pos;
        pHeader->Timestamp = (CAN_RDT0R_TIME & hcan->Instance->sFIFOMailBox[RxFifo].RDTR) >> CAN_RDT0R_TIME_Pos;
        
        CAN_ID_EXT                  (0x00000004U)  /*!< Extended Id */

        typedef struct
        {
          uint32_t StdId;    /*!< Specifies the standard identifier.
                                  This parameter must be a number between Min_Data = 0 and Max_Data = 0x7FF. */

          uint32_t ExtId;    /*!< Specifies the extended identifier.
                                  This parameter must be a number between Min_Data = 0 and Max_Data = 0x1FFFFFFF. */

          uint32_t IDE;      /*!< Specifies the type of identifier for the message that will be transmitted.
                                  This parameter can be a value of @ref CAN_identifier_type */

          uint32_t RTR;      /*!< Specifies the type of frame for the message that will be transmitted.
                                  This parameter can be a value of @ref CAN_remote_transmission_request */

          uint32_t DLC;      /*!< Specifies the length of the frame that will be transmitted.
                                  This parameter must be a number between Min_Data = 0 and Max_Data = 8. */

          uint32_t Timestamp; /*!< Specifies the timestamp counter value captured on start of frame reception.
                                  @note: Time Triggered Communication Mode must be enabled.
                                  This parameter must be a number between Min_Data = 0 and Max_Data = 0xFFFF. */

          uint32_t FilterMatchIndex; /*!< Specifies the index of matching acceptance filter element.
                                          This parameter must be a number between Min_Data = 0 and Max_Data = 0xFF. */

        } CAN_RxHeaderTypeDef;
        """

        # set extended CAN identifier:
        qemu.write_memory(can_rxheader_ptr+8, 4, 4, 1)
        qemu.write_memory(can_rxheader_ptr+4, 4, can_extid, 1)

        time.sleep(2)
        # that should be enough:

        # define HAL_OK 0x00U; (retval)
        return True, 0

    @bp_handler(['HAL_CAN_GetRxFifoFillLevel'])
    def handle_canqueue_fifolevel_check(self, qemu, bp_addr):

        can_id_ptr = qemu.regs.r0
        rxfifo = qemu.regs.r1

        # #define CAN_RF0R_FMP0_Pos      (0U)
        # #define CAN_RF0R_FMP0_Msk      (0x3UL << CAN_RF0R_FMP0_Pos)
        # #define CAN_RF0R_FMP0          CAN_RF0R_FMP0_Msk) 
        # Only handle FIFO 0
        log.info("RXFIFO Queue is %d" % (rxfifo))
        if rxfifo != 0:
            log.info("HAL_CAN_GetRxFifoFillLevel: FIFO 1 Requested, ignoring")
            return False, None

        queue_size = len(self.model.rx_queue[0])

        if queue_size!=0:
            log.warn("RXFIFO: QUEUE SIZE: %d" % queue_size)
        # No need to do anything else
        # Report number of messages
        
        time.sleep(2)
        
        return True, queue_size

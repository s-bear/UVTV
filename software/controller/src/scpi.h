#include "scpi/scpi.h"

typedef struct _scpi_help_t {
    const char *syntax, *description;
} scpi_help_t;

#define SCPI_HELP_LIST_END {NULL, NULL}

#define SCPI_CMDS_BASIC \
    {"*IDN?", SCPI_CoreIdnQ, 0}, \
    {"*RST", SCPI_CoreRst, 0}, \
    {"SYSTem:ERRor[:NEXT]?", SCPI_SystemErrorNextQ, 0}, \
    {"SYSTem:ERRor:COUNt?", SCPI_SystemErrorCountQ, 0}

#define SCPI_HELP_BASIC                                 \
    {"*IDN?", "Identification"},                        \
    {"*RST", "Software Reset"},                         \
    {"SYSTem:ERRor[:NEXT]?", "Pop first error in queue."}, \
    {"SYSTem:ERRor:COUNt?", "Number of unread errors."}

#define SCPI_CMDS_IEEE_488_2 \
    {"*CLS", SCPI_CoreCls, 0}, \
    {"*ESE", SCPI_CoreEse, 0}, \
    {"*ESE?", SCPI_CoreEseQ, 0}, \
    {"*ESR?", SCPI_CoreEsrQ, 0}, \
    {"*IDN?", SCPI_CoreIdnQ, 0}, \
    {"*OPC", SCPI_CoreOpc, 0}, \
    {"*OPC?", SCPI_CoreOpcQ, 0}, \
    {"*RST", SCPI_CoreRst, 0}, \
    {"*SRE", SCPI_CoreSre, 0}, \
    {"*SRE?", SCPI_CoreSreQ, 0}, \
    {"*STB?", SCPI_CoreStbQ, 0}, \
    {"*TST?", SCPI_CoreTstQ, 0}, \
    {"*WAI", SCPI_CoreWai, 0}

#define SCPI_HELP_IEEE_488_2  \
    {"*CLS", "Clear Status"},     \
    {"*ESE[?]", "Standard Event Status Enable"},         \
    {"*ESR?", "Standard Event Status Register"}, \
    {"*IDN?", "Identification"}, \
    {"*OPC[?]", "Operation Complete"}, \
    {"*RST", "Software Reset"}, \
    {"*SRE[?]", "Service Request Enable"},         \
    {"*STB?", "Status Byte"}, \
    {"*TST?", "Self Test"}, \
    {"*WAI", "Wait-to-continue"}

#define SCPI_CMDS_SCPI_99 \
    {"SYSTem:VERSion?", SCPI_SystemVersionQ, 0}, \
    {"SYSTem:ERRor[:NEXT]?", SCPI_SystemErrorNextQ, 0}, \
    {"SYSTem:ERRor:COUNt?", SCPI_SystemErrorCountQ, 0}, \
    {"STATus:QUEStionable[:EVENt]?", SCPI_StatusQuestionableEventQ, 0}, \
    {"STATus:QUEStionable:CONDition?", SCPI_StatusQuestionableConditionQ, 0}, \
    {"STATus:QUEStionable:ENABle?", SCPI_StatusQuestionableEnableQ, 0}, \
    {"STATus:QUEStionable:ENABle", SCPI_StatusQuestionableEnable, 0}, \
    {"STATus:OPERation:CONDition?", SCPI_StatusOperationConditionQ, 0}, \
    {"STATus:OPERation[:EVENt]?", SCPI_StatusOperationEventQ, 0}, \
    {"STATus:OPERation:ENABle?", SCPI_StatusOperationEnableQ, 0}, \
    {"STATus:OPERation:ENABle", SCPI_StatusOperationEnable, 0}, \
    {"STATus:PRESet", SCPI_StatusPreset, 0}

#define SCPI_HELP_SCPI_99 \
    {"SYSTem:VERSion?", "SCPI version"}, \
    {"SYSTem:ERRor[:NEXT]?", "Pop first error in queue."}, \
    {"SYSTem:ERRor:COUNt?", "Number of unread errors."}, \
    {"STATus:QUEStionable[:EVENt]?", "Read and clear the questionable event register"}, \
    {"STATus:QUEStionable:CONDition?", "Bits indicate questionable operation"}, \
    {"STATus:QUEStionable:ENABle[?]", "Bit mask setting which events are reported in the summary bit"}, \
    {"STATus:OPERation:CONDition?", "Operation condition register"}, \
    {"STATus:OPERation[:EVENt]?", "Read and clear the operation event register"}, \
    {"STATus:OPERation:ENABle[?]", "Bit mask setting which events are reported in the summary bit"}, \
    {"STATus:PRESet", "Enable all status registers"}

    /*
scpi_result_t scpi_control(scpi_t *ctx, scpi_ctrl_name_t ctrl, scpi_reg_val_t val) {
  const char* name = "UNKNOWN";
  switch(ctrl) {
      case SCPI_CTRL_SRQ: name = "SERVICE REQUEST"; break;
      case SCPI_CTRL_GTL: name = "GO TO LOCAL"; break;
      case SCPI_CTRL_SDC: name = "SELECTED DEVICE CLEAR"; break;
      case SCPI_CTRL_PPC: name = "PARALLEL POLL CONFIGURE"; break;
      case SCPI_CTRL_GET: name = "GROUP EXECUTE TRIGGER"; break;
      case SCPI_CTRL_TCT: name = "TAKE CONTROL"; break;
      case SCPI_CTRL_LLO: name = "DEVICE CLEAR"; break;
      case SCPI_CTRL_DCL: name = "LOCAL LOCKOUT"; break;
      case SCPI_CTRL_PPU: name = "PARALLEL POLL UNCONFIGURE"; break;
      case SCPI_CTRL_SPE: name = "SERIAL POLL ENABLE"; break;
      case SCPI_CTRL_SPD: name = "SERIAL POLL DISABLE"; break;
      case SCPI_CTRL_MLA: name = "MY LOCAL ADDRESS"; break;
      case SCPI_CTRL_UNL: name = "UNLISTEN"; break;
      case SCPI_CTRL_MTA: name = "MY TALK ADDRESS"; break;
      case SCPI_CTRL_UNT: name = "UNTALK"; break;
      case SCPI_CTRL_MSA: name = "MY SECONDARY ADDRESS"; break;
  }
  SER.printf("**CTRL: %s: 0x%X\r\n", name, val);
  return SCPI_RES_OK;
} // */
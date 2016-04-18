#include <string>
#include <iostream>

std::string GetSetting(const std::string settingName) {{
    if (settingName == "overwrite_oadb_period")
      return "{overwrite_oadb_period}";
    else if (settingName == "workdir")
      return "{workdir}";
    else if (settingName == "datadir")
      return "{datadir}";
    else if (settingName == "data_pattern")
      return "{data_pattern}";
    else if (settingName == "run_number_prefix")
      return "{run_number_prefix}";
    else if (settingName == "run_list")
      return "{run_list}";
    else if (settingName == "is_mc")
      return "{is_mc}";
    else if (settingName == "datatype")
      return "{datatype}";
    else if (settingName == "runmode")
      return "{runmode}";
    else 
      std::cout << "Invalid setting name: " << settingName << std::endl;
  }};


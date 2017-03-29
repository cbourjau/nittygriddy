// This file is automatically created. Do not edit it!  If you see
// this in the nittygriddy source code, the double curly brackets are
// for escaping!

#include <string>
#include <iostream>

std::string GetSetting(const std::string settingName) {{
    if (settingName == "workdir")
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
    else if (settingName == "nworkers")
      return "{nworkers}";
    else if (settingName == "wait_for_gdb")
      return "{wait_for_gdb}";
    else if (settingName == "par_files")
      return "{par_files}";
    else if (settingName == "aliphysics_version")
      return "{aliphysics_version}";
    else if (settingName == "ttl")
      return "{ttl}";
    else if (settingName == "max_files_subjob")
      return "{max_files_subjob}";
    else if (settingName == "use_train_conf")
      return "{use_train_conf}";
    else if (settingName == "")
      std::cout << "Invalid setting name: " << settingName << std::endl;
    return "";
  }};


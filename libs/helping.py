helping = {
    'endpoint': {
        'title': 'Ввод URL сервера',
        'text': """
[ref=https://vk.com/im][color=548cb9]https://vk.com/im[/color][/ref]
    """
    },
    'menu': {
        'title': 'Меню',
        'text': """
IAPWS essentials:
        
    * P: Pressure, [MPa]
    * T: Temperature, [K]
    * g: Specific Gibbs free energy, [kJ/kg]
    * a: Specific Helmholtz free energy, [kJ/kg]
    * v: Specific volume, [m³/kg]
    * rho: Density, [kg/m³]
    * h: Specific enthalpy, [kJ/kg]
    * u: Specific internal energy, [kJ/kg]
    * s: Specific entropy, [kJ/kg·K]
    * cp: Specific isobaric heat capacity, [kJ/kg·K]
    * cv: Specific isochoric heat capacity, [kJ/kg·K]
    * Z: Compression factor, [-]
    * fi: Fugacity coefficient, [-]
    * f: Fugacity, [MPa]

    * gamma: Isoentropic exponent, [-]
    * alfav: Isobaric cubic expansion coefficient, [1/K]
    * xkappa: Isothermal compressibility, [1/MPa]
    * kappas: Adiabatic compresibility, [1/MPa]
    * alfap: Relative pressure coefficient, [1/K]
    * betap: Isothermal stress coefficient, [kg/m³]
    * joule: Joule-Thomson coefficient, [K/MPa]
    * deltat: Isothermal throttling coefficient, [kJ/kg·MPa]
    * region: Region

    * v0: Ideal specific volume, [m³/kg]
    * u0: Ideal specific internal energy, [kJ/kg]
    * h0: Ideal specific enthalpy, [kJ/kg]
    * s0: Ideal specific entropy, [kJ/kg·K]
    * a0: Ideal specific Helmholtz free energy, [kJ/kg]
    * g0: Ideal specific Gibbs free energy, [kJ/kg]
    * cp0: Ideal specific isobaric heat capacity, [kJ/kg·K]
    * cv0: Ideal specific isochoric heat capacity [kJ/kg·K]
    * w0: Ideal speed of sound, [m/s]
    * gamma0: Ideal isoentropic exponent, [-]

    * w: Speed of sound, [m/s]
    * mu: Dynamic viscosity, [Pa·s]
    * nu: Kinematic viscosity, [m²/s]
    * k: Thermal conductivity, [W/m·K]
    * alfa: Thermal diffusivity, [m²/s]
    * sigma: Surface tension, [N/m]
    * epsilon: Dielectric constant, [-]
    * n: Refractive index, [-]
    * Prandt: Prandtl number, [-]
    * Pr: Reduced Pressure, [-]
    * Tr: Reduced Temperature, [-]
    * Hvap: Vaporization heat, [kJ/kg]
    * Svap: Vaporization entropy, [kJ/kg·K]

    Examples
    --------
    {cp, T = 170 + K, x = 0.5, phase = 'Liquid'} # Output: 4.3695
    {cp, T = 170 + K, x = 0.5, phase = 'Vapor'} # Output: 2.5985
    {w, T = 170 + K, x = 0.5, phase = 'Liquid'} # Output: 1418.3
    {w, T = 170 + K, x = 0.5, phase = 'Vapor'} # Output: 498.78

    {P, T = 325 + K, x = 0.5} # Output: 12.0505
    {v, T = 325 + K, x = 0.5, phase = 'Liquid'} # Output: 0.00152830
    {v, T = 325 + K, x = 0.5, phase = 'Vapor'} # Output: 0.0141887
    {h, T = 325 + K, x = 0.5, phase = 'Liquid'} # Output: 1493.37
    {h, T = 325 + K, x = 0.5, phase = 'Vapor'} # Output: 2684.48

    {cp0, T = 50 + K, P = 0.0006112127} # Output: 1.8714
    {cv0, T = 50 + K, P = 0.0006112127} # Output: 1.4098
    {h0, T = 50 + K, P = 0.0006112127} # Output: 2594.66
    {s0, T = 50 + K, P = 0.0006112127} # Output: 9.471
    {w0, T = 50 + K, P = 0.0006112127} # Output: 444.93
    """
    },
}

expression_help = \
"""IAPWS expression parameters:


add_multiple_graphs
menu
endpoint

graph_settings
graph_new_indirect_variable_naming
graph_variable_choosing
graph_rename_variable
graph_expression
graph_spectral_buffer_size
graph_avg_buffer_size
graph_target_value
graph_precision

control_settings
control_name
control_variable_choosing
control_icon_on
control_icon_off


    * P: Pressure, [MPa]
    * T: Temperature, [K]
    * g: Specific Gibbs free energy, [kJ/kg]
    * a: Specific Helmholtz free energy, [kJ/kg]
    * v: Specific volume, [m³/kg]
    * rho: Density, [kg/m³]
    * h: Specific enthalpy, [kJ/kg]
    * u: Specific internal energy, [kJ/kg]
    * s: Specific entropy, [kJ/kg·K]
    * cp: Specific isobaric heat capacity, [kJ/kg·K]
    * cv: Specific isochoric heat capacity, [kJ/kg·K]
    * Z: Compression factor, [-]
    * fi: Fugacity coefficient, [-]
    * f: Fugacity, [MPa]

    * gamma: Isoentropic exponent, [-]
    * alfav: Isobaric cubic expansion coefficient, [1/K]
    * xkappa: Isothermal compressibility, [1/MPa]
    * kappas: Adiabatic compresibility, [1/MPa]
    * alfap: Relative pressure coefficient, [1/K]
    * betap: Isothermal stress coefficient, [kg/m³]
    * joule: Joule-Thomson coefficient, [K/MPa]
    * deltat: Isothermal throttling coefficient, [kJ/kg·MPa]
    * region: Region

    * v0: Ideal specific volume, [m³/kg]
    * u0: Ideal specific internal energy, [kJ/kg]
    * h0: Ideal specific enthalpy, [kJ/kg]
    * s0: Ideal specific entropy, [kJ/kg·K]
    * a0: Ideal specific Helmholtz free energy, [kJ/kg]
    * g0: Ideal specific Gibbs free energy, [kJ/kg]
    * cp0: Ideal specific isobaric heat capacity, [kJ/kg·K]
    * cv0: Ideal specific isochoric heat capacity [kJ/kg·K]
    * w0: Ideal speed of sound, [m/s]
    * gamma0: Ideal isoentropic exponent, [-]

    * w: Speed of sound, [m/s]
    * mu: Dynamic viscosity, [Pa·s]
    * nu: Kinematic viscosity, [m²/s]
    * k: Thermal conductivity, [W/m·K]
    * alfa: Thermal diffusivity, [m²/s]
    * sigma: Surface tension, [N/m]
    * epsilon: Dielectric constant, [-]
    * n: Refractive index, [-]
    * Prandt: Prandtl number, [-]
    * Pr: Reduced Pressure, [-]
    * Tr: Reduced Temperature, [-]
    * Hvap: Vaporization heat, [kJ/kg]
    * Svap: Vaporization entropy, [kJ/kg·K]

    Examples
    --------
    {cp, T = 170 + K, x = 0.5, phase = 'Liquid'} # Output: 4.3695
    {cp, T = 170 + K, x = 0.5, phase = 'Vapor'} # Output: 2.5985
    {w, T = 170 + K, x = 0.5, phase = 'Liquid'} # Output: 1418.3
    {w, T = 170 + K, x = 0.5, phase = 'Vapor'} # Output: 498.78

    {P, T = 325 + 273.15, x = 0.5} # Output: 12.0505
    {v, T = 325 + 273.15, x = 0.5, phase = 'Liquid'} # Output: 0.00152830
    {v, T = 325 + 273.15, x = 0.5, phase = 'Vapor'} # Output: 0.0141887
    {h, T = 325 + 273.15, x = 0.5, phase = 'Liquid'} # Output: 1493.37
    {h, T = 325 + 273.15, x = 0.5, phase = 'Vapor'} # Output: 2684.48

    {cp0, T = 50 + K, P = 0.0006112127} # Output: 1.8714
    {cv0, T = 50 + K, P = 0.0006112127} # Output: 1.4098
    {h0, T = 50 + K, P = 0.0006112127} # Output: 2594.66
    {s0, T = 50 + K, P = 0.0006112127} # Output: 9.471
    {w0, T = 50 + K, P = 0.0006112127} # Output: 444.93
    """
      PROGRAM GFDECO
C===============================================================================
C Gradient Factor Decompression Program in FORTRAN
C
C Author: Erik C. Baker
C
C "DISTRIBUTE FREELY - CREDIT THE AUTHOR"
C
C Notes:
C 1. This program uses the sixteen (16) half-time compartments of the
C Buhlmann ZH-L16 model. The optional Compartment 1b is used here with
C half-times of 1.88 minutes for helium and 5.0 minutes for nitrogen.
C Conservatism and deep stops are introduced in the decompression
C profiles by use of gradient factors.
C
C 2. This program uses various DEC, IBM, and Microsoft extensions which
C may not be supported by all FORTRAN compilers. Comments are made with
C a capital "C" in the first column or an exclamation point "!" placed
C in a line after code. An asterisk "*" in column 6 is a continuation
C of the previous line. All code, except for line numbers, starts in
C column 7.
C
C 3. Comments and suggestions for improvements are welcome. Please
C respond by e-mail to: EBaker@se.aeieng.com
CC==============================================================================
      IMPLICIT NONE
C===============================================================================
C LOCAL VARIABLES - MAIN PROGRAM
C===============================================================================
      CHARACTER M*1, OS_Command*3, Word*7, Units*3
      CHARACTER Line1*70
      CHARACTER Units_Word1*4, Units_Word2*7, Units_Word3*6
      CHARACTER Units_Word4*5, Altitude_Dive_Algorithm*3
      INTEGER I, J !loop counters
      INTEGER*2 Month, Day, Year, Clock_Hour, Minute
      INTEGER Number_of_Mixes, Number_of_Changes, Profile_Code
      INTEGER Repetitive_Dive_Flag
      LOGICAL Altitude_Dive_Algorithm_Off
      REAL Deco_Ceiling_Depth, Deco_Stop_Depth, Step_Size
      REAL Sum_of_Fractions, Sum_Check
      REAL Depth, Ending_Depth, Starting_Depth
      REAL Rate, Rounding_Operation1, Run_Time_End_of_Segment
      REAL Last_Run_Time, Stop_Time, Depth_Start_of_Deco_Zone
      REAL Rounding_Operation2, Deepest_Possible_Stop_Depth
      REAL Next_Stop
      REAL Surface_Interval_Time
      REAL RMV_During_Dive, RMV_During_Deco
      REAL Gradient_Factor_Lo, Gradient_Factor_Hi, Factor_Slope
      REAL Gradient_Factor_Current_Stop, Gradient_Factor_Next_Stop
C===============================================================================
C LOCAL ARRAYS - MAIN PROGRAM
C===============================================================================
      INTEGER Mix_Change(10)
      REAL Depth_Change (10)
      REAL Rate_Change(10), Step_Size_Change(10)
      REAL Helium_Half_Time(16), Nitrogen_Half_Time(16)
C===============================================================================
C GLOBAL CONSTANTS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Water_Vapor_Pressure
      COMMON /Block_8/ Water_Vapor_Pressure
      REAL Minimum_Deco_Stop_Time
      COMMON /Block_21/ Minimum_Deco_Stop_Time
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      INTEGER Segment_Number
      REAL Run_Time, Segment_Time
      COMMON /Block_2/ Run_Time, Segment_Number, Segment_Time
      REAL Ending_Ambient_Pressure
      COMMON /Block_4/ Ending_Ambient_Pressure
      INTEGER Mix_Number
      COMMON /Block_9/ Mix_Number
      REAL Barometric_Pressure
      COMMON /Block_18/ Barometric_Pressure
      LOGICAL Units_Equal_Fsw, Units_Equal_Msw
      COMMON /Block_15/ Units_Equal_Fsw, Units_Equal_Msw
      REAL Units_Factor
      COMMON /Block_16/ Units_Factor
      REAL Running_CNS, Running_OTU
      COMMON /Block_32/ Running_CNS, Running_OTU
      REAL Altitude_of_Dive
      COMMON /Block_33/ Altitude_of_Dive
      REAL Gradient_Factor
      COMMON /Block_37/ Gradient_Factor
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Helium_Time_Constant(16)
      COMMON /Block_1A/ Helium_Time_Constant
      REAL Nitrogen_Time_Constant(16)
      COMMON /Block_1B/ Nitrogen_Time_Constant
      REAL Helium_Pressure(16), Nitrogen_Pressure(16)
      COMMON /Block_3/ Helium_Pressure, Nitrogen_Pressure
      REAL Fraction_Helium(10), Fraction_Nitrogen(10)
      COMMON /Block_5/ Fraction_Helium, Fraction_Nitrogen
      REAL Fraction_Oxygen(10)
      COMMON /Block_30/ Fraction_Oxygen
      REAL Running_Gas_Volume(10)
      COMMON /Block_31/ Running_Gas_Volume
      REAL AHE(16), BHE(16), AN2(16), BN2(16)
      COMMON /Block_34/ AHE, BHE, AN2, BN2
      REAL Coefficient_AHE(16), Coefficient_BHE(16)
      REAL Coefficient_AN2(16), Coefficient_BN2(16)
      COMMON /Block_35/ Coefficient_AHE, Coefficient_BHE,
     * Coefficient_AN2, Coefficient_BN2
C===============================================================================
C NAMELIST FOR PROGRAM SETTINGS (READ IN FROM ASCII TEXT FILE)
C===============================================================================
      NAMELIST /Program_Settings/ Units, Altitude_Dive_Algorithm,
     * Minimum_Deco_Stop_Time, Gradient_Factor_Lo,
     * Gradient_Factor_Hi, RMV_During_Dive,
     * RMV_During_Deco
C===============================================================================
C ASSIGN HALF-TIME VALUES TO BUHLMANN COMPARTMENT ARRAYS
C===============================================================================
      DATA Helium_Half_Time(1)/1.88/,Helium_Half_Time(2)/3.02/,
     * Helium_Half_Time(3)/4.72/,Helium_Half_Time(4)/6.99/,
     * Helium_Half_Time(5)/10.21/,Helium_Half_Time(6)/14.48/,
     * Helium_Half_Time(7)/20.53/,Helium_Half_Time(8)/29.11/,
     * Helium_Half_Time(9)/41.20/,Helium_Half_Time(10)/55.19/,
     * Helium_Half_Time(11)/70.69/,Helium_Half_Time(12)/90.34/,
     * Helium_Half_Time(13)/115.29/,Helium_Half_Time(14)/147.42/,
     * Helium_Half_Time(15)/188.24/,Helium_Half_Time(16)/240.03/
      DATA Nitrogen_Half_Time(1)/5.0/,Nitrogen_Half_Time(2)/8.0/,
     * Nitrogen_Half_Time(3)/12.5/,Nitrogen_Half_Time(4)/18.5/,
     * Nitrogen_Half_Time(5)/27.0/,Nitrogen_Half_Time(6)/38.3/,
     * Nitrogen_Half_Time(7)/54.3/,Nitrogen_Half_Time(8)/77.0/,
     * Nitrogen_Half_Time(9)/109.0/,Nitrogen_Half_Time(10)/146.0/,
     * Nitrogen_Half_Time(11)/187.0/,Nitrogen_Half_Time(12)/239.0/,
     * Nitrogen_Half_Time(13)/305.0/,Nitrogen_Half_Time(14)/390.0/,
     * Nitrogen_Half_Time(15)/498.0/,Nitrogen_Half_Time(16)/635.0/
C===============================================================================
C OPEN FILES FOR PROGRAM INPUT/OUTPUT
C===============================================================================
      OPEN (UNIT = 7, FILE = 'GFDECO.IN', STATUS = 'UNKNOWN',
     * ACCESS = 'SEQUENTIAL', FORM = 'FORMATTED')
      OPEN (UNIT = 8, FILE = 'GFDECO.OUT', STATUS = 'UNKNOWN',
     * ACCESS = 'SEQUENTIAL', FORM = 'FORMATTED')
      OPEN (UNIT = 10, FILE = 'GFDECO.SET', STATUS = 'UNKNOWN',
     * ACCESS = 'SEQUENTIAL', FORM = 'FORMATTED')
      OPEN (UNIT = 13, FILE = 'DIVEDATA.OUT', STATUS = 'UNKNOWN',
     * ACCESS = 'SEQUENTIAL', FORM = 'FORMATTED')
C===============================================================================
C BEGIN PROGRAM EXECUTION WITH OUTPUT MESSAGE TO SCREEN
C===============================================================================
      OS_Command = 'CLS'
C     CALL SYSTEMQQ (OS_Command) !Pass "clear screen" command
      PRINT *,' ' !to MS operating system
      PRINT *,'PROGRAM GFDECO'
      PRINT *,' ' !asterisk indicates print to screen
C===============================================================================
C READ IN PROGRAM SETTINGS AND CHECK FOR ERRORS
C IF THERE ARE ERRORS, WRITE AN ERROR MESSAGE AND TERMINATE PROGRAM
C===============================================================================
      READ (10,Program_Settings)
      IF ((Units .EQ. 'fsw').OR.(Units .EQ. 'FSW')) THEN
      Units_Equal_Fsw = (.TRUE.)
      Units_Equal_Msw = (.FALSE.)
      ELSE IF ((Units .EQ. 'msw').OR.(Units .EQ. 'MSW')) THEN
      Units_Equal_Fsw = (.FALSE.)
      Units_Equal_Msw = (.TRUE.)
      ELSE
C     CALL SYSTEMQQ (OS_Command)
      WRITE (*,901)
      WRITE (*,900)
      STOP 'PROGRAM TERMINATED'
      END IF
      IF ((Altitude_Dive_Algorithm .EQ. 'ON') .OR.
     * (Altitude_Dive_Algorithm .EQ. 'on')) THEN
      Altitude_Dive_Algorithm_Off = (.FALSE.)
      ELSE IF ((Altitude_Dive_Algorithm .EQ. 'OFF') .OR.
     * (Altitude_Dive_Algorithm .EQ. 'off')) THEN
      Altitude_Dive_Algorithm_Off = (.TRUE.)
      ELSE
      WRITE (*,902)
      WRITE (*,900)
      STOP 'PROGRAM TERMINATED'
      END IF
C===============================================================================
C INITIALIZE CONSTANTS/VARIABLES BASED ON SELECTION OF UNITS - FSW OR MSW
C fsw = feet of seawater, a unit of pressure
C msw = meters of seawater, a unit of pressure
C===============================================================================
      IF (Units_Equal_Fsw) THEN
      WRITE (*,800)
      Units_Word1 = 'fswg'
      Units_Word2 = 'fsw/min'
      Units_Word3 = ' (scf)'
      Units_Word4 = ' acf'
      Units_Factor = 33.0
      Water_Vapor_Pressure = 1.848 !based on respiratory quotient of 0.9
      !(U.S. Navy value)
      DO I = 1,16
      Coefficient_AHE(I) = AHE(I) * 3.25684678
      Coefficient_BHE(I) = BHE(I)
      Coefficient_AN2(I) = AN2(I) * 3.25684678
      Coefficient_BN2(I) = BN2(I)
      END DO
      END IF
      IF (Units_Equal_Msw) THEN
      WRITE (*,801)
      Units_Word1 = 'mswg'
      Units_Word2 = 'msw/min'
      Units_Word3 = 'liters'
      Units_Word4 = 'liter'
      Units_Factor = 10.1325
      Water_Vapor_Pressure = 0.567 !based on respiratory quotient of 0.9
      !(U.S. Navy value)
      DO I = 1,16
      Coefficient_AHE(I) = AHE(I)
      Coefficient_BHE(I) = BHE(I)
      Coefficient_AN2(I) = AN2(I)
      Coefficient_BN2(I) = BN2(I)
      END DO
      END IF
C===============================================================================
C INITIALIZE CONSTANTS/VARIABLES
C===============================================================================
      Run_Time = 0.0
      Segment_Number = 0
      Gradient_Factor = Gradient_Factor_Lo
      DO I = 1,16
      Helium_Time_Constant(I) = ALOG(2.0)/Helium_Half_Time(I)
      Nitrogen_Time_Constant(I) = ALOG(2.0)/Nitrogen_Half_Time(I)
      END DO
C===============================================================================
C INITIALIZE VARIABLES FOR SEA LEVEL OR ALTITUDE DIVE
C===============================================================================
      IF (Altitude_Dive_Algorithm_Off) THEN
      Altitude_of_Dive = 0.0
      CALL CALC_BAROMETRIC_PRESSURE (Altitude_of_Dive) !subroutine
      WRITE (*,802) Altitude_of_Dive, Barometric_Pressure
      DO I = 1,16
      Helium_Pressure(I) = 0.0
      Nitrogen_Pressure(I) = (Barometric_Pressure -
     * Water_Vapor_Pressure)*0.79
      END DO
      ELSE
      CALL ALTITUDE_DIVE_SUBPROGRAM !subroutine
      END IF
C===============================================================================
C START OF REPETITIVE DIVE LOOP
C This is the largest loop in the main program and operates between Lines
C 30 and 330. If there is one or more repetitive dives, the program will
C return to this point to process each repetitive dive.
C===============================================================================
30    DO 330, WHILE (.TRUE.) !loop will run continuously until
      !there is an exit statement
C===============================================================================
C INPUT DIVE DESCRIPTION AND GAS MIX DATA FROM ASCII TEXT INPUT FILE
C BEGIN WRITING HEADINGS/OUTPUT TO ASCII TEXT OUTPUT FILES
C===============================================================================
      READ (7,805) Line1
C     CALL CLOCK (Year, Month, Day, Clock_Hour, Minute, M) !subroutine
      WRITE (8,811)
      WRITE (8,812)
      WRITE (8,813)
      WRITE (8,813)
C     WRITE (8,814) Month, Day, Year, Clock_Hour, Minute, M
      WRITE (8,813)
      WRITE (8,815) Line1
      WRITE (8,813)
      WRITE (13,811)
      WRITE (13,812)
      WRITE (13,813)
      WRITE (13,813)
      WRITE (13,814) Month, Day, Year, Clock_Hour, Minute, M
      WRITE (13,813)
      WRITE (13,815) Line1
      IF (Units_Equal_Fsw) THEN
      WRITE (13,813)
      WRITE (13,610) Altitude_of_Dive, Barometric_Pressure,
     * (Barometric_Pressure/33.0)*1013.25
      WRITE (13,813)
      END IF
      IF (Units_Equal_Msw) THEN
      WRITE (13,813)
      WRITE (13,611) Altitude_of_Dive, Barometric_Pressure,
     * (Barometric_Pressure/10.0)*1000.0
      WRITE (13,813)
      END IF
      READ (7,*) Number_of_Mixes !check for errors in gasmixes
      DO I = 1, Number_of_Mixes
      READ (7,*) Fraction_Oxygen(I), Fraction_Helium(I),
     * Fraction_Nitrogen(I)
      Sum_of_Fractions = Fraction_Oxygen(I) + Fraction_Helium(I) +
     * Fraction_Nitrogen(I)
      Sum_Check = Sum_of_Fractions
      IF (Sum_Check .NE. 1.0) THEN
C     CALL SYSTEMQQ (OS_Command)
      WRITE (*,906)
      WRITE (*,900)
      STOP 'PROGRAM TERMINATED'
      END IF
      END DO
      WRITE (8,820)
      DO J = 1, Number_of_Mixes
      WRITE (8,821) J, Fraction_Oxygen(J), Fraction_Helium(J),
     * Fraction_Nitrogen(J)
      END DO
      DO I = 1, Number_of_Mixes
      Running_Gas_Volume(I) = 0.0
      END DO
      WRITE (8,813)
      WRITE (8,813)
      WRITE (8,830)
      WRITE (8,813)
      WRITE (8,831)
      WRITE (8,832)
      WRITE (8,833) Units_Word1, Units_Word1, Units_Word2, Units_Word1
      WRITE (8,834)
      WRITE (13,813)
      WRITE (13,600)
      WRITE (13,813)
      WRITE (13,601)
      WRITE (13,602) Units_Word4
      WRITE (13,603) Units_Word3, Units_Word1, Units_Word1, Units_Word1
      WRITE (13,604)
C===============================================================================
C DIVE PROFILE LOOP - INPUT DIVE PROFILE DATA FROM ASCII TEXT INPUT FILE
C AND PROCESS DIVE AS A SERIES OF ASCENT/DESCENT AND CONSTANT DEPTH
C SEGMENTS. THIS ALLOWS FOR MULTI-LEVEL (DESCENDING) DIVE PROFILES. NOTE
C THAT THE DECO CEILING IS NOT CHECKED DURING THE DIVE PROFILE SO USERS
C MUST NOT ENTER AN ASCENT SEGMENT THAT WOULD VIOLATE A DECO CEILING.
C THE GAS LOADINGS FOR EACH SEGMENT OF THE DIVE PROFILE ARE UPDATED.
C Profile codes: 1 = Ascent/Descent, 2 = Constant Depth, 99 = Decompress
C===============================================================================
      DO WHILE (.TRUE.) !loop will run continuously until
      !there is an exit statement
      READ (7,*) Profile_Code
      IF (Profile_Code .EQ. 1) THEN
      READ (7,*) Starting_Depth, Ending_Depth, Rate, Mix_Number
      CALL GAS_LOADINGS_ASCENT_DESCENT (Starting_Depth, !subroutine
     * Ending_Depth, Rate)
      IF (Ending_Depth .GT. Starting_Depth) THEN
      Word = 'Descent'
      ELSE IF (Starting_Depth .GT. Ending_Depth) THEN
      Word = 'Ascent '
      ELSE
      Word = 'ERROR'
      END IF
      WRITE (8,840) Segment_Number, Segment_Time, Run_Time,
     * Mix_Number, Word, Starting_Depth, Ending_Depth,
     * Rate
      CALL DIVEDATA_ASCENT_DESCENT (Starting_Depth, Ending_Depth,!subroutine
     * Rate, RMV_During_Dive)
      ELSE IF (Profile_Code .EQ. 2) THEN
      READ (7,*) Depth, Run_Time_End_of_Segment, Mix_Number
      CALL GAS_LOADINGS_CONSTANT_DEPTH (Depth, !subroutine
     * Run_Time_End_of_Segment)
      WRITE (8,845) Segment_Number, Segment_Time, Run_Time,
     * Mix_Number, Depth
      CALL DIVEDATA_CONSTANT_DEPTH (Depth, RMV_During_Dive) !subroutine
      ELSE IF (Profile_Code .EQ. 99) THEN
      EXIT
      ELSE
C     CALL SYSTEMQQ (OS_Command)
      WRITE (*,907)
      WRITE (*,900)
      STOP 'PROGRAM TERMINATED'
      END IF
      END DO
C===============================================================================
C INPUT PARAMETERS TO BE USED FOR STAGED DECOMPRESSION AND SAVE IN ARRAYS.
C ASSIGN INITAL PARAMETERS TO BE USED AT START OF ASCENT
C The user has the ability to change mix, ascent rate, and step size in any
C combination at any depth during the ascent.
C===============================================================================
      READ (7,*) Number_of_Changes
      DO I = 1, Number_of_Changes
      READ (7,*) Depth_Change(I), Mix_Change(I), Rate_Change(I),
     * Step_Size_Change(I)
      END DO
      Starting_Depth = Depth_Change(1)
      Mix_Number = Mix_Change(1)
      Rate = Rate_Change(1)
      Step_Size = Step_Size_Change(1)
      Last_Run_Time = 0.0
C===============================================================================
C CALCULATE THE DEPTH WHERE THE DECOMPRESSION ZONE BEGINS FOR THIS PROFILE
C BASED ON THE INITIAL ASCENT PARAMETERS AND WRITE THE DEEPEST POSSIBLE
C DECOMPRESSION STOP DEPTH TO THE OUTPUT FILE
C Knowing where the decompression zone starts is very important. Below
C that depth there is no possibility for bubble formation because there
C will be no supersaturation gradients. Deco stops should never start
C below the deco zone. The deepest possible stop deco stop depth is
C defined as the next "standard" stop depth above the point where the
C leading compartment enters the deco zone. Thus, the program will not
C base this calculation on step sizes larger than 10 fsw or 3 msw. The
C deepest possible stop depth is not used in the program, per se, rather
C it is information to tell the diver where to start putting on the brakes
C during ascent. This should be prominently displayed by any deco program.
C===============================================================================
      CALL CALC_START_OF_DECO_ZONE (Starting_Depth, Rate, !subroutine
     * Depth_Start_of_Deco_Zone)
      IF (Units_Equal_Fsw) THEN
      IF (Step_Size .LT. 10.0) THEN
      Rounding_Operation1 =
     * (Depth_Start_of_Deco_Zone/Step_Size) - 0.5
      Deepest_Possible_Stop_Depth = ANINT(Rounding_Operation1)
     * * Step_Size
      ELSE
      Rounding_Operation1 = (Depth_Start_of_Deco_Zone/10.0)
     * - 0.5
      Deepest_Possible_Stop_Depth = ANINT(Rounding_Operation1)
     * * 10.0
      END IF
      END IF
      IF (Units_Equal_Msw) THEN
      IF (Step_Size .LT. 3.0) THEN
      Rounding_Operation1 =
     * (Depth_Start_of_Deco_Zone/Step_Size) - 0.5
      Deepest_Possible_Stop_Depth = ANINT(Rounding_Operation1)
     * * Step_Size
      ELSE
      Rounding_Operation1 = (Depth_Start_of_Deco_Zone/3.0)
     * - 0.5
      Deepest_Possible_Stop_Depth = ANINT(Rounding_Operation1)
     * * 3.0
      END IF
      END IF
      WRITE (8,813)
      WRITE (8,813)
      WRITE (8,850)
      WRITE (8,813)
      WRITE (8,857) Depth_Start_of_Deco_Zone, Units_Word1
      WRITE (8,858) Deepest_Possible_Stop_Depth, Units_Word1
      WRITE (8,813)
      WRITE (8,851)
      WRITE (8,852)
      WRITE (8,853) Units_Word1, Units_Word2, Units_Word1
      WRITE (8,854)
C===============================================================================
C CALCULATE CURRENT DECO CEILING AND SET FIRST DECO STOP. CHECK TO MAKE
C SURE THAT SELECTED STEP SIZE WILL NOT ROUND UP FIRST STOP TO A DEPTH THAT
C IS BELOW THE DECO ZONE.
C===============================================================================
      CALL CALC_DECO_CEILING (Deco_Ceiling_Depth) !subroutine
      IF (Deco_Ceiling_Depth .LE. 0.0) THEN
      Deco_Stop_Depth = 0.0
      ELSE
      Rounding_Operation2 = (Deco_Ceiling_Depth/Step_Size) + 0.5
      Deco_Stop_Depth = ANINT(Rounding_Operation2) * Step_Size
      END IF
      IF (Deco_Stop_Depth .GT. Depth_Start_of_Deco_Zone) THEN
      WRITE (*,905)
      WRITE (*,900)
      STOP 'PROGRAM TERMINATED'
      END IF
C===============================================================================
C PERFORM A SEPARATE "PROJECTED ASCENT" OUTSIDE OF THE MAIN PROGRAM TO MAKE
C SURE THAT AN INCREASE IN GAS LOADINGS DURING ASCENT TO THE FIRST STOP WILL
C NOT CAUSE A VIOLATION OF THE DECO CEILING. IF SO, ADJUST THE FIRST STOP
C DEEPER BASED ON STEP SIZE UNTIL A SAFE ASCENT CAN BE MADE.
C Note: this situation is a possibility when ascending from extremely deep
C dives or due to an unusual gas mix selection.
C CHECK AGAIN TO MAKE SURE THAT ADJUSTED FIRST STOP WILL NOT BE BELOW THE
C DECO ZONE.
C===============================================================================
      CALL PROJECTED_ASCENT (Starting_Depth, Rate, !subroutine
     * Deco_Stop_Depth, Step_Size)
      IF (Deco_Stop_Depth .GT. Depth_Start_of_Deco_Zone) THEN
      WRITE (*,905)
      WRITE (*,900)
      STOP 'PROGRAM TERMINATED'
      END IF
C===============================================================================
C SET GRADIENT FACTOR SLOPE
C===============================================================================
      IF (Deco_Stop_Depth .GT. 0.0) THEN
      Factor_Slope = (Gradient_Factor_Hi - Gradient_Factor_Lo)/
     * (0.0 - Deco_Stop_Depth)
      END IF
C===============================================================================
C DECO STOP LOOP BLOCK FOR DECOMPRESSION SCHEDULE
C===============================================================================
      DO WHILE (.TRUE.) !loop will run continuously until
      !there is an exit statement
      CALL GAS_LOADINGS_ASCENT_DESCENT (Starting_Depth, !subroutine
     * Deco_Stop_Depth, Rate)
      CALL DIVEDATA_ASCENT_DESCENT (Starting_Depth, !subroutine
     * Deco_Stop_Depth, Rate, RMV_During_Deco)
      WRITE (8,860) Segment_Number, Segment_Time, Run_Time,
     * Mix_Number, Deco_Stop_Depth, Rate
      IF (Deco_Stop_Depth .EQ. 0.0) THEN
      WRITE (8,861) Gradient_Factor
      END IF
      IF (Deco_Stop_Depth .LE. 0.0) EXIT !exit at Line 80
      IF (Number_of_Changes .GT. 1) THEN
      DO I = 2, Number_of_Changes
      IF (Depth_Change(I) .GE. Deco_Stop_Depth) THEN
      Mix_Number = Mix_Change(I)
      Rate = Rate_Change(I)
      Step_Size = Step_Size_Change(I)
      END IF
      END DO
      END IF
      Gradient_Factor_Current_Stop = Gradient_Factor
      Next_Stop = Deco_Stop_Depth - Step_Size
      Gradient_Factor_Next_Stop = Next_Stop * Factor_Slope +
     * Gradient_Factor_Hi
      Gradient_Factor = Gradient_Factor_Next_Stop
      CALL DECOMPRESSION_STOP (Deco_Stop_Depth, Step_Size) !subroutine
      CALL DIVEDATA_CONSTANT_DEPTH (Deco_Stop_Depth, !subroutine
     * RMV_During_Deco)
C===============================================================================
C This next bit justs rounds up the stop time at the first stop to be in
C whole increments of the minimum stop time (to make for a nice deco table).
C===============================================================================
      IF (Last_Run_Time .EQ. 0.0) THEN
      Stop_Time =
     * ANINT((Segment_Time/Minimum_Deco_Stop_Time) + 0.5) *
     * Minimum_Deco_Stop_Time
      ELSE
      Stop_Time = Run_Time - Last_Run_Time
      END IF
C===============================================================================
C IF MINIMUM STOP TIME PARAMETER IS A WHOLE NUMBER (i.e. 1 minute) THEN
C WRITE DECO SCHEDULE USING INTEGER NUMBERS (looks nicer). OTHERWISE, USE
C DECIMAL NUMBERS.
C Note: per the request of a noted exploration diver(!), program now allows
C a minimum stop time of less than one minute so that total ascent time can
C be minimized on very long dives. In fact, with step size set at 1 fsw or
C 0.2 msw and minimum stop time set at 0.1 minute (6 seconds), a near
C continuous decompression schedule can be computed.
C===============================================================================
      IF (AINT(Minimum_Deco_Stop_Time) .EQ.
     * Minimum_Deco_Stop_Time) THEN
      WRITE (8,862) Segment_Number, Segment_Time, Run_Time,
     * Mix_Number, Gradient_Factor_Current_Stop,
     * INT(Deco_Stop_Depth),
     * INT(Stop_Time), INT(Run_Time)
      ELSE
      WRITE (8,863) Segment_Number, Segment_Time, Run_Time,
     * Mix_Number, Gradient_Factor_Current_Stop,
     * Deco_Stop_Depth, Stop_Time,
     * Run_Time
      END IF
      Starting_Depth = Deco_Stop_Depth
      Deco_Stop_Depth = Next_Stop
      Last_Run_Time = Run_Time
80    END DO !end of deco stop loop block
C===============================================================================
C Write to DIVEDATA output file
C===============================================================================
      WRITE (13,701)
      WRITE (13,702) Running_CNS, Running_OTU
      WRITE (13,703)
      WRITE (13,813)
      WRITE (13,813)
      WRITE (13,704)
      WRITE (13,705) Units_Word3
      DO I = 1, Number_of_Mixes
      WRITE (13,706) I, Running_Gas_Volume(I),
     * Running_Gas_Volume(I)*1.5
      END DO
C===============================================================================
C PROCESSING OF DIVE COMPLETE. READ INPUT FILE TO DETERMINE IF THERE IS A
C REPETITIVE DIVE. IF NONE, THEN EXIT REPETITIVE LOOP.
C===============================================================================
      READ (7,*) Repetitive_Dive_Flag
      IF (Repetitive_Dive_Flag .EQ. 0) THEN
      EXIT !exit repetitive dive loop
      !at Line 330
C===============================================================================
C IF THERE IS A REPETITIVE DIVE, COMPUTE GAS LOADINGS (OFF-GASSING) DURING
C SURFACE INTERVAL TIME. RE-INITIALIZE SELECTED VARIABLES AND RETURN TO
C START OF REPETITIVE LOOP AT LINE 30.
C===============================================================================
      ELSE IF (Repetitive_Dive_Flag .EQ. 1) THEN
      READ (7,*) Surface_Interval_Time
      CALL GAS_LOADINGS_SURFACE_INTERVAL (Surface_Interval_Time) !subroutine
      Run_Time = 0.0
      Segment_Number = 0
      Gradient_Factor = Gradient_Factor_Lo
      Running_CNS = 0.0
      Running_OTU = 0.0
      WRITE (8,890)
      WRITE (8,813)
      WRITE (13,890)
      WRITE (13,813)
      CYCLE !Return to start of repetitive loop to process another dive
C===============================================================================
C WRITE ERROR MESSAGE AND TERMINATE PROGRAM IF THERE IS AN ERROR IN THE
C INPUT FILE FOR THE REPETITIVE DIVE FLAG
C===============================================================================
      ELSE
C     CALL SYSTEMQQ (OS_Command)
      WRITE (*,908)
      WRITE (*,900)
      STOP 'PROGRAM TERMINATED'
      END IF
330   CONTINUE !End of repetitive loop
C===============================================================================
C FINAL WRITES TO OUTPUT AND CLOSE PROGRAM FILES
C===============================================================================
      WRITE (*,813)
      WRITE (*,871)
      WRITE (*,872)
      WRITE (*,813)
      CLOSE (UNIT = 7, STATUS = 'KEEP')
      CLOSE (UNIT = 8, STATUS = 'KEEP')
      CLOSE (UNIT = 10, STATUS = 'KEEP')
      CLOSE (UNIT = 13, STATUS = 'KEEP')
C===============================================================================
C FORMAT STATEMENTS - PROGRAM INPUT/OUTPUT
C===============================================================================
800   FORMAT ('0UNITS = FEET OF SEAWATER (FSW)')
801   FORMAT ('0UNITS = METERS OF SEAWATER (MSW)')
802   FORMAT ('0ALTITUDE = ',1X,F7.1,4X,'BAROMETRIC PRESSURE = ',
     *F6.3)
805   FORMAT (A70)
810   FORMAT ('7E7&a10L7&l80F7&l8D7(s0p16.67h8.5')
811   FORMAT (26X,'DECOMPRESSION CALCULATION PROGRAM')
812   FORMAT (24X,'Developed in FORTRAN by Erik C. Baker')
814   FORMAT ('Program Run:',4X,I2.2,'-',I2.2,'-',I4,1X,'at',1X,I2.2,
     * ':',I2.2,1X,A1,'m',23X,'Model: ZH-L16B/GF')
815   FORMAT ('Description:',4X,A70)
813   FORMAT (' ')
820   FORMAT ('Gasmix Summary:',24X,'FO2',4X,'FHe',4X,'FN2')
821   FORMAT (26X,'Gasmix #',I2,2X,F5.3,2X,F5.3,2X,F5.3)
830   FORMAT (36X,'DIVE PROFILE')
831   FORMAT ('Seg-',2X,'Segm.',2X,'Run',3X,'|',1X,'Gasmix',1X,'|',1X,
     * 'Ascent',4X,'From',5X,'To',6X,'Rate',4X,'|',1X,'Constant')
832   FORMAT ('ment',2X,'Time',3X,'Time',2X,'|',2X,'Used',2X,'|',3X,
     * 'or',5X,'Depth',3X,'Depth',4X,'+Dn/-Up',2X,'|',2X,'Depth')
833   FORMAT (2X,'#',3X,'(min)',2X,'(min)',1X,'|',4X,'#',3X,'|',1X,
     * 'Descent',2X,'(',A4,')',2X,'(',A4,')',2X,'(',A7,')',1X,
     * '|',2X,'(',A4,')')
834   FORMAT ('-----',1X,'-----',2X,'-----',1X,'|',1X,'------',1X,'|',
     * 1X,'-------',2X,'------',2X,'------',2X,'---------',1X,
     * '|',1X,'--------')
840   FORMAT (I3,3X,F5.1,1X,F6.1,1X,'|',3X,I2,3X,'|',1X,A7,F7.0,
     * 1X,F7.0,3X,F7.1,3X,'|')
845   FORMAT (I3,3X,F5.1,1X,F6.1,1X,'|',3X,I2,3X,'|',36X,'|',F7.0)
850   FORMAT (31X,'DECOMPRESSION PROFILE')
851   FORMAT ('Seg-',2X,'Segm.',2X,'Run',3X,'|',1X,'Gasmix',1X,'|',1X,
     * 'Ascent',3X,'Ascent',9X,'|',2X,'DECO',3X,'STOP',
     * 3X,'RUN')
852   FORMAT ('ment',2X,'Time',3X,'Time',2X,'|',2X,'Used',2X,'|',3X,
     * 'To',6X,'Rate',4X,'Grad.',1X,'|',2X,'STOP',3X,'TIME',
     * 3X,'TIME')
853   FORMAT (2X,'#',3X,'(min)',2X,'(min)',1X,'|',4X,'#',3X,'|',1X,
     * '(',A4,')',1X,'(',A7,')',1X,'Factor',1X,'|',1X,'(',A4,')',
     * 2X,'(min)',2X,'(min)')
854   FORMAT ('-----',1X,'-----',2X,'-----',1X,'|',1X,'------',1X,'|',
     * 1X,'------',1X,'---------',1X,'------',1X,'|',1X,
     * '------',2X,'-----',2X,'-----')
857   FORMAT (10X,'Leading compartment enters the decompression zone',
     * 1X,'at',F7.1,1X,A4)
858   FORMAT (17X,'Deepest possible decompression stop is',F7.1,1X,A4)
860   FORMAT (I3,3X,F5.1,1X,F6.1,1X,'|',3X,I2,3X,'|',2X,F4.0,3X,F6.1,
     * 10X,'|')
861   FORMAT (48X,F4.2,2X,'|')
862   FORMAT (I3,3X,F5.1,1X,F6.1,1X,'|',3X,I2,3X,'|',19X,F4.2,2X,'|',
     * 2X,I4,3X,I4,2X,I5)
863   FORMAT (I3,3X,F5.1,1X,F6.1,1X,'|',3X,I2,3X,'|',19X,F4.2,2X,'|',
     * 2X,F5.0,1X,F6.1,1X,F7.1)
871   FORMAT (' PROGRAM CALCULATIONS COMPLETE')
872   FORMAT ('0Output data is located in the files GFDECO.OUT and DIVED
     *ATA.OUT')
890   FORMAT ('REPETITIVE DIVE:')
891   FORMAT (F8.3)
701   FORMAT (58X,'------',2X,'-----')
702   FORMAT (56X,2P,F7.1,'%',0P,F7.1)
703   FORMAT (59X,'Total',2X,'Total')
704   FORMAT (50X,'with 1.5')
705   FORMAT ('Gasmix Volume Totals:',18X,A6,3X,'safety factor')
706   FORMAT (25X,'Gasmix #',I2,3X,F7.1,5X,F7.1)
600   FORMAT (37X,'DIVE DATA')
601   FORMAT ('Seg-',2X,'Segm.',2X,'Run',3X,'|',1X,'Gasmix',1X,'|',2X,
     * 'RMV',2X,'GasVol',3X,'Max',3X,'Max',5X,'CNS',4X,'CPTD',4X,
     * 'END',5X,'END')
602   FORMAT ('ment',2X,'Time',3X,'Time',2X,'|',2X,'Used',2X,'|',A5,
     * 3X,'Segm.',2X,'Depth',2X,'PO2',5X,'O2 %',3X,
     * '(OTU)',3X,'N2',5X,'N2+O2')
603   FORMAT (2X,'#',3X,'(min)',2X,'(min)',1X,'|',4X,'#',3X,'|',1X,
     * '/min',2X,A6,2X,'(',A4,')',1X,'Segm.',3X,'Segm.',2X,
     * 'Segm.',2X,'(',A4,')',2X,'(',A4,')')
604   FORMAT ('-----',1X,'-----',2X,'-----',1X,'|',1X,'------',1X,'|',
     * 1X,'----',2X,'------',2X,'------',1X,'-----',2X,'------',
     * 2X,'-----',2X,'------',2X,'------')
610   FORMAT ('Altitude =',F8.1,1X,'feet',4X,'Barometric Pressure =',
     * F5.1,1X,'fsw abs. (',F7.2,1X,'millibars)')
611   FORMAT ('Altitude =',F8.1,1X,'meters',4X,'Barometric Pressure =',
     * F5.1,1X,'msw abs. (',F7.2,1X,'millibars)')
C===============================================================================
C FORMAT STATEMENTS - ERROR MESSAGES
C===============================================================================
900   FORMAT (' ')
901   FORMAT ('0ERROR! UNITS MUST BE FSW OR MSW')
902   FORMAT ('0ERROR! ALTITUDE DIVE ALGORITHM MUST BE ON OR OFF')
905   FORMAT ('0ERROR! STEP SIZE IS TOO LARGE TO DECOMPRESS')
906   FORMAT ('0ERROR IN INPUT FILE (GASMIX DATA)')
907   FORMAT ('0ERROR IN INPUT FILE (PROFILE CODE)')
908   FORMAT ('0ERROR IN INPUT FILE (REPETITIVE DIVE CODE)')
C===============================================================================
C END OF MAIN PROGRAM
C===============================================================================
      END
C===============================================================================
C NOTE ABOUT PRESSURE UNITS USED IN CALCULATIONS:
C It is the convention in decompression calculations to compute all gas
C loadings, absolute pressures, partial pressures, etc., in the units of
C depth pressure that you are diving - either feet of seawater (fsw) or
C meters of seawater (msw). This program follows that convention.
C===============================================================================
C===============================================================================
C FUNCTION SUBPROGRAM FOR GAS LOADING CALCULATIONS - ASCENT AND DESCENT
C===============================================================================
      FUNCTION SCHREINER_EQUATION (Initial_Inspired_Gas_Pressure,
     *Rate_Change_Insp_Gas_Pressure, Interval_Time, Gas_Time_Constant,
     *Initial_Gas_Pressure)
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Initial_Inspired_Gas_Pressure !input
      REAL Rate_Change_Insp_Gas_Pressure !input
      REAL Interval_Time, Gas_Time_Constant !input
      REAL Initial_Gas_Pressure !input
      REAL SCHREINER_EQUATION !output
C===============================================================================
C Note: The Schreiner equation is applied when calculating the uptake or
C elimination of compartment gases during linear ascents or descents at a
C constant rate. For ascents, a negative number for rate must be used.
C===============================================================================
      SCHREINER_EQUATION =
     *Initial_Inspired_Gas_Pressure + Rate_Change_Insp_Gas_Pressure*
     *(Interval_Time - 1.0/Gas_Time_Constant) -
     *(Initial_Inspired_Gas_Pressure - Initial_Gas_Pressure -
     *Rate_Change_Insp_Gas_Pressure/Gas_Time_Constant)*
     *EXP (-Gas_Time_Constant*Interval_Time)
      RETURN
      END
C===============================================================================
C FUNCTION SUBPROGRAM FOR GAS LOADING CALCULATIONS - CONSTANT DEPTH
C===============================================================================
      FUNCTION HALDANE_EQUATION (Initial_Gas_Pressure,
     *Inspired_Gas_Pressure, Gas_Time_Constant, Interval_Time)
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Initial_Gas_Pressure, Inspired_Gas_Pressure !input
      REAL Gas_Time_Constant, Interval_Time !input
      REAL HALDANE_EQUATION !output
C===============================================================================
C Note: The Haldane equation is applied when calculating the uptake or
C elimination of compartment gases during intervals at constant depth (the
C outside ambient pressure does not change).
C===============================================================================
      HALDANE_EQUATION = Initial_Gas_Pressure +
     *(Inspired_Gas_Pressure - Initial_Gas_Pressure)*
     *(1.0 - EXP(-Gas_Time_Constant * Interval_Time))
      RETURN
      END
C===============================================================================
C SUBROUTINE GAS_LOADINGS_ASCENT_DESCENT
C Purpose: This subprogram applies the Schreiner equation to update the
C gas loadings (partial pressures of helium and nitrogen) in the half-time
C compartments due to a linear ascent or descent segment at a constant rate.
C===============================================================================
      SUBROUTINE GAS_LOADINGS_ASCENT_DESCENT (Starting_Depth,
     * Ending_Depth, Rate)
      IMPLICIT NONE
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Starting_Depth, Ending_Depth, Rate !input
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      INTEGER I !loop counter
      INTEGER Last_Segment_Number
      REAL Initial_Inspired_He_Pressure
      REAL Initial_Inspired_N2_Pressure
      REAL Last_Run_Time
      REAL Helium_Rate, Nitrogen_Rate, Starting_Ambient_Pressure
      REAL SCHREINER_EQUATION !function subprogram
C===============================================================================
C GLOBAL CONSTANTS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Water_Vapor_Pressure
      COMMON /Block_8/ Water_Vapor_Pressure
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      INTEGER Segment_Number !both input
      REAL Run_Time, Segment_Time !and output
      COMMON /Block_2/ Run_Time, Segment_Number, Segment_Time
      REAL Ending_Ambient_Pressure !output
      COMMON /Block_4/ Ending_Ambient_Pressure
      INTEGER Mix_Number
      COMMON /Block_9/ Mix_Number
      REAL Barometric_Pressure
      COMMON /Block_18/ Barometric_Pressure
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Helium_Time_Constant(16)
      COMMON /Block_1A/ Helium_Time_Constant
      REAL Nitrogen_Time_Constant(16)
      COMMON /Block_1B/ Nitrogen_Time_Constant
      REAL Helium_Pressure(16), Nitrogen_Pressure(16) !both input
      COMMON /Block_3/ Helium_Pressure, Nitrogen_Pressure !and output
      REAL Fraction_Helium(10), Fraction_Nitrogen(10)
      COMMON /Block_5/ Fraction_Helium, Fraction_Nitrogen
      REAL Initial_Helium_Pressure(16), Initial_Nitrogen_Pressure(16) !output
      COMMON /Block_23/ Initial_Helium_Pressure,
     * Initial_Nitrogen_Pressure
C===============================================================================
C CALCULATIONS
C===============================================================================
      Segment_Time = (Ending_Depth - Starting_Depth)/Rate
      Last_Run_Time = Run_Time
      Run_Time = Last_Run_Time + Segment_Time
      Last_Segment_Number = Segment_Number
      Segment_Number = Last_Segment_Number + 1
      Ending_Ambient_Pressure = Ending_Depth + Barometric_Pressure
      Starting_Ambient_Pressure = Starting_Depth + Barometric_Pressure
      Initial_Inspired_He_Pressure = (Starting_Ambient_Pressure -
     * Water_Vapor_Pressure)*Fraction_Helium(Mix_Number)
      Initial_Inspired_N2_Pressure = (Starting_Ambient_Pressure -
     * Water_Vapor_Pressure)*Fraction_Nitrogen(Mix_Number)
      Helium_Rate = Rate*Fraction_Helium(Mix_Number)
      Nitrogen_Rate = Rate*Fraction_Nitrogen(Mix_Number)
      DO I = 1,16
      Initial_Helium_Pressure(I) = Helium_Pressure(I)
      Initial_Nitrogen_Pressure(I) = Nitrogen_Pressure(I)
      Helium_Pressure(I) = SCHREINER_EQUATION
     * (Initial_Inspired_He_Pressure, Helium_Rate,
     * Segment_Time, Helium_Time_Constant(I),
     * Initial_Helium_Pressure(I))
      Nitrogen_Pressure(I) = SCHREINER_EQUATION
     * (Initial_Inspired_N2_Pressure, Nitrogen_Rate,
     * Segment_Time, Nitrogen_Time_Constant(I),
     * Initial_Nitrogen_Pressure(I))
      END DO
C===============================================================================
C END OF SUBROUTINE
C===============================================================================
      RETURN
      END
C===============================================================================
C SUBROUTINE GAS_LOADINGS_CONSTANT_DEPTH
C Purpose: This subprogram applies the Haldane equation to update the
C gas loadings (partial pressures of helium and nitrogen) in the half-time
C compartments for a segment at constant depth.
C===============================================================================
      SUBROUTINE GAS_LOADINGS_CONSTANT_DEPTH (Depth,
     * Run_Time_End_of_Segment)
      IMPLICIT NONE
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Depth, Run_Time_End_of_Segment !input
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      INTEGER I !loop counter
      INTEGER Last_Segment_Number
      REAL Initial_Helium_Pressure, Initial_Nitrogen_Pressure
      REAL Inspired_Helium_Pressure, Inspired_Nitrogen_Pressure
      REAL Ambient_Pressure, Last_Run_Time
      REAL HALDANE_EQUATION !function subprogram
C===============================================================================
C GLOBAL CONSTANTS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Water_Vapor_Pressure
      COMMON /Block_8/ Water_Vapor_Pressure
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      INTEGER Segment_Number !both input
      REAL Run_Time, Segment_Time !and output
      COMMON /Block_2/ Run_Time, Segment_Number, Segment_Time
      REAL Ending_Ambient_Pressure !output
      COMMON /Block_4/ Ending_Ambient_Pressure
      INTEGER Mix_Number
      COMMON /Block_9/ Mix_Number
      REAL Barometric_Pressure
      COMMON /Block_18/ Barometric_Pressure
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Helium_Time_Constant(16)
      COMMON /Block_1A/ Helium_Time_Constant
      REAL Nitrogen_Time_Constant(16)
      COMMON /Block_1B/ Nitrogen_Time_Constant
      REAL Helium_Pressure(16), Nitrogen_Pressure(16) !both input
      COMMON /Block_3/ Helium_Pressure, Nitrogen_Pressure !and output
      REAL Fraction_Helium(10), Fraction_Nitrogen(10)
      COMMON /Block_5/ Fraction_Helium, Fraction_Nitrogen
C===============================================================================
C CALCULATIONS
C===============================================================================
      Segment_Time = Run_Time_End_of_Segment - Run_Time
      Last_Run_Time = Run_Time_End_of_Segment
      Run_Time = Last_Run_Time
      Last_Segment_Number = Segment_Number
      Segment_Number = Last_Segment_Number + 1
      Ambient_Pressure = Depth + Barometric_Pressure
      Inspired_Helium_Pressure = (Ambient_Pressure -
     * Water_Vapor_Pressure)*Fraction_Helium(Mix_Number)
      Inspired_Nitrogen_Pressure = (Ambient_Pressure -
     * Water_Vapor_Pressure)*Fraction_Nitrogen(Mix_Number)
      Ending_Ambient_Pressure = Ambient_Pressure
      DO I = 1,16
      Initial_Helium_Pressure = Helium_Pressure(I)
      Initial_Nitrogen_Pressure = Nitrogen_Pressure(I)
      Helium_Pressure(I) = HALDANE_EQUATION
     * (Initial_Helium_Pressure, Inspired_Helium_Pressure,
     * Helium_Time_Constant(I), Segment_Time)
      Nitrogen_Pressure(I) = HALDANE_EQUATION
     * (Initial_Nitrogen_Pressure, Inspired_Nitrogen_Pressure,
     * Nitrogen_Time_Constant(I), Segment_Time)
      END DO
C===============================================================================
C END OF SUBROUTINE
C===============================================================================
      RETURN
      END
C===============================================================================
C SUBROUTINE CALC_DECO_CEILING
C Purpose: This subprogram calculates the deco ceiling (the safe ascent
C depth) in each compartment, based on M-values modifed by gradient factors,
C and then finds the deepest deco ceiling across all compartments. This
C deepest value (Deco Ceiling Depth) is then used by the Decompression Stop
C subroutine to determine the actual deco schedule.
C===============================================================================
      SUBROUTINE CALC_DECO_CEILING (Deco_Ceiling_Depth)
      IMPLICIT NONE
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Deco_Ceiling_Depth !output
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      INTEGER I !loop counter
      REAL Gas_Loading
      REAL Tolerated_Ambient_Pressure
      REAL Coefficient_A, Coefficient_B
C===============================================================================
C LOCAL ARRAYS
C===============================================================================
      REAL Compartment_Deco_Ceiling(16)
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Barometric_Pressure
      COMMON /Block_18/ Barometric_Pressure
      REAL Gradient_Factor
      COMMON /Block_37/ Gradient_Factor
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Helium_Pressure(16), Nitrogen_Pressure(16) !input
      COMMON /Block_3/ Helium_Pressure, Nitrogen_Pressure
      REAL Coefficient_AHE(16), Coefficient_BHE(16)
      REAL Coefficient_AN2(16), Coefficient_BN2(16)
      COMMON /Block_35/ Coefficient_AHE, Coefficient_BHE,
     * Coefficient_AN2, Coefficient_BN2
C===============================================================================
C CALCULATIONS
C===============================================================================
      DO I = 1,16
      Gas_Loading = Helium_Pressure(I) + Nitrogen_Pressure(I)
      Coefficient_A = (Helium_Pressure(I)*Coefficient_AHE(I) +
     * Nitrogen_Pressure(I)*Coefficient_AN2(I))/
     * Gas_Loading
      Coefficient_B = (Helium_Pressure(I)*Coefficient_BHE(I) +
     * Nitrogen_Pressure(I)*Coefficient_BN2(I))/
     * Gas_Loading
      Tolerated_Ambient_Pressure = (Gas_Loading - Coefficient_A*
     * Gradient_Factor)/(Gradient_Factor/Coefficient_B -
     * Gradient_Factor + 1.0)
C===============================================================================
C The tolerated ambient pressure cannot be less than zero absolute, i.e.,
C the vacuum of outer space!
C===============================================================================
      IF (Tolerated_Ambient_Pressure .LT. 0.0) THEN
      Tolerated_Ambient_Pressure = 0.0
      END IF
C===============================================================================
C The Deco Ceiling Depth is computed in a loop after all of the individual
C compartment deco ceilings have been calculated. It is important that the
C Deco Ceiling Depth (max deco ceiling across all compartments) only be
C extracted from the compartment values and not be compared against some
C initialization value. For example, if MAX(Deco_Ceiling_Depth . .) was
C compared against zero, this could cause a program lockup because sometimes
C the Deco Ceiling Depth needs to be negative (but not less than absolute
C zero) in order to decompress to the last stop at zero depth.
C===============================================================================
      Compartment_Deco_Ceiling(I) =
     * Tolerated_Ambient_Pressure - Barometric_Pressure
      END DO
      Deco_Ceiling_Depth = Compartment_Deco_Ceiling(1)
      DO I = 2,16
      Deco_Ceiling_Depth =
     * MAX(Deco_Ceiling_Depth, Compartment_Deco_Ceiling(I))
      END DO
C===============================================================================
C END OF SUBROUTINE
C===============================================================================
      RETURN
      END
C===============================================================================
C SUBROUTINE CALC_START_OF_DECO_ZONE
C Purpose: This subroutine uses the Bisection Method to find the depth at
C which the leading compartment just enters the decompression zone.
C Source: "Numerical Recipes in Fortran 77", Cambridge University Press,
C 1992.
C===============================================================================
      SUBROUTINE CALC_START_OF_DECO_ZONE (Starting_Depth, Rate,
     * Depth_Start_of_Deco_Zone)
      IMPLICIT NONE
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Starting_Depth, Rate, Depth_Start_of_Deco_Zone !input
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      INTEGER I, J !loop counters
      REAL Initial_Helium_Pressure, Initial_Nitrogen_Pressure
      REAL Initial_Inspired_He_Pressure
      REAL Initial_Inspired_N2_Pressure
      REAL Time_to_Start_of_Deco_Zone, Helium_Rate, Nitrogen_Rate
      REAL Starting_Ambient_Pressure
      REAL Cpt_Depth_Start_of_Deco_Zone, Low_Bound, High_Bound
      REAL High_Bound_Helium_Pressure, High_Bound_Nitrogen_Pressure
      REAL Mid_Range_Helium_Pressure, Mid_Range_Nitrogen_Pressure
      REAL Function_at_High_Bound, Function_at_Low_Bound, Mid_Range_Time
      REAL Function_at_Mid_Range, Differential_Change, Last_Diff_Change
      REAL SCHREINER_EQUATION !function subprogram
C===============================================================================
C GLOBAL CONSTANTS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Water_Vapor_Pressure
      COMMON /Block_8/ Water_Vapor_Pressure
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      INTEGER Mix_Number
      COMMON /Block_9/ Mix_Number
      REAL Barometric_Pressure
      COMMON /Block_18/ Barometric_Pressure
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Helium_Time_Constant(16)
      COMMON /Block_1A/ Helium_Time_Constant
      REAL Nitrogen_Time_Constant(16)
      COMMON /Block_1B/ Nitrogen_Time_Constant
      REAL Helium_Pressure(16), Nitrogen_Pressure(16)
      COMMON /Block_3/ Helium_Pressure, Nitrogen_Pressure
      REAL Fraction_Helium(10), Fraction_Nitrogen(10)
      COMMON /Block_5/ Fraction_Helium, Fraction_Nitrogen
C===============================================================================
C CALCULATIONS
C First initialize some variables
C===============================================================================
      Depth_Start_of_Deco_Zone = 0.0
      Starting_Ambient_Pressure = Starting_Depth + Barometric_Pressure
      Initial_Inspired_He_Pressure = (Starting_Ambient_Pressure -
     * Water_Vapor_Pressure)*Fraction_Helium(Mix_Number)
      Initial_Inspired_N2_Pressure = (Starting_Ambient_Pressure -
     * Water_Vapor_Pressure)*Fraction_Nitrogen(Mix_Number)
      Helium_Rate = Rate * Fraction_Helium(Mix_Number)
      Nitrogen_Rate = Rate * Fraction_Nitrogen(Mix_Number)
C===============================================================================
C ESTABLISH THE BOUNDS FOR THE ROOT SEARCH USING THE BISECTION METHOD
C AND CHECK TO MAKE SURE THAT THE ROOT WILL BE WITHIN BOUNDS. PROCESS
C EACH COMPARTMENT INDIVIDUALLY AND FIND THE MAXIMUM DEPTH ACROSS ALL
C COMPARTMENTS (LEADING COMPARTMENT)
C In this case, we are solving for time - the time when the gas tension in
C the compartment will be equal to ambient pressure. The low bound for time
C is set at zero and the high bound is set at the time it would take to
C ascend to zero ambient pressure (absolute). Since the ascent rate is
C negative, a multiplier of -1.0 is used to make the time positive. The
C desired point when gas tension equals ambient pressure is found at a time
C somewhere between these endpoints. The algorithm checks to make sure that
C the solution lies in between these bounds by first computing the low bound
C and high bound function values.
C===============================================================================
      Low_Bound = 0.0
      High_Bound = -1.0*(Starting_Ambient_Pressure/Rate)
      DO 200 I = 1,16
      Initial_Helium_Pressure = Helium_Pressure(I)
      Initial_Nitrogen_Pressure = Nitrogen_Pressure(I)
      Function_at_Low_Bound = Initial_Helium_Pressure +
     * Initial_Nitrogen_Pressure - Starting_Ambient_Pressure
      High_Bound_Helium_Pressure = SCHREINER_EQUATION
     * (Initial_Inspired_He_Pressure, Helium_Rate,
     * High_Bound, Helium_Time_Constant(I),
     * Initial_Helium_Pressure)
      High_Bound_Nitrogen_Pressure = SCHREINER_EQUATION
     * (Initial_Inspired_N2_Pressure, Nitrogen_Rate,
     * High_Bound, Nitrogen_Time_Constant(I),
     * Initial_Nitrogen_Pressure)
      Function_at_High_Bound = High_Bound_Helium_Pressure +
     * High_Bound_Nitrogen_Pressure
      IF ((Function_at_High_Bound * Function_at_Low_Bound) .GE. 0.0)
     * THEN
      PRINT *,'ERROR! ROOT IS NOT WITHIN BRACKETS'
C      PAUSE
      END IF
C===============================================================================
C APPLY THE BISECTION METHOD IN SEVERAL ITERATIONS UNTIL A SOLUTION WITH
C THE DESIRED ACCURACY IS FOUND
C Note: the program allows for up to 100 iterations. Normally an exit will
C be made from the loop well before that number. If, for some reason, the
C program exceeds 100 iterations, there will be a pause to alert the user.
C===============================================================================
      IF (Function_at_Low_Bound .LT. 0.0) THEN
      Time_to_Start_of_Deco_Zone = Low_Bound
      Differential_Change = High_Bound - Low_Bound
      ELSE
      Time_to_Start_of_Deco_Zone = High_Bound
      Differential_Change = Low_Bound - High_Bound
      END IF
      DO 150 J = 1, 100
      Last_Diff_Change = Differential_Change
      Differential_Change = Last_Diff_Change*0.5
      Mid_Range_Time = Time_to_Start_of_Deco_Zone +
     * Differential_Change
      Mid_Range_Helium_Pressure = SCHREINER_EQUATION
     * (Initial_Inspired_He_Pressure, Helium_Rate,
     * Mid_Range_Time, Helium_Time_Constant(I),
     * Initial_Helium_Pressure)
      Mid_Range_Nitrogen_Pressure = SCHREINER_EQUATION
     * (Initial_Inspired_N2_Pressure, Nitrogen_Rate,
     * Mid_Range_Time, Nitrogen_Time_Constant(I),
     * Initial_Nitrogen_Pressure)
      Function_at_Mid_Range =
     * Mid_Range_Helium_Pressure +
     * Mid_Range_Nitrogen_Pressure -
     * (Starting_Ambient_Pressure + Rate*Mid_Range_Time)
      IF (Function_at_Mid_Range .LE. 0.0)
     * Time_to_Start_of_Deco_Zone = Mid_Range_Time
      IF ((ABS(Differential_Change) .LT. 1.0E-3) .OR.
     * (Function_at_Mid_Range .EQ. 0.0)) GOTO 170
150   CONTINUE
      PRINT *,'ERROR! ROOT SEARCH EXCEEDED MAXIMUM ITERATIONS'
C      PAUSE
C===============================================================================
C When a solution with the desired accuracy is found, the program jumps out
C of the loop to Line 170 and assigns the solution value for the individual
C compartment.
C===============================================================================
170   Cpt_Depth_Start_of_Deco_Zone = (Starting_Ambient_Pressure +
     * Rate*Time_to_Start_of_Deco_Zone) - Barometric_Pressure
C===============================================================================
C The overall solution will be the compartment with the maximum depth where
C gas tension equals ambient pressure (leading compartment).
C===============================================================================
      Depth_Start_of_Deco_Zone = MAX(Depth_Start_of_Deco_Zone,
     * Cpt_Depth_Start_of_Deco_Zone)
200   CONTINUE
C===============================================================================
C END OF SUBROUTINE
C===============================================================================
      RETURN
      END
C===============================================================================
C SUBROUTINE PROJECTED_ASCENT
C Purpose: This subprogram performs a simulated ascent outside of the main
C program to ensure that a deco ceiling will not be violated due to unusual
C gas loading during ascent (on-gassing). If the deco ceiling is violated,
C the stop depth will be adjusted deeper by the step size until a safe
C ascent can be made.
C===============================================================================
      SUBROUTINE PROJECTED_ASCENT (Starting_Depth, Rate,
     * Deco_Stop_Depth, Step_Size)
      IMPLICIT NONE
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Starting_Depth, Rate, Step_Size !input
      REAL Deco_Stop_Depth !input and output
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      INTEGER I !loop counter
      REAL Initial_Inspired_He_Pressure, Initial_Inspired_N2_Pressure
      REAL Helium_Rate, Nitrogen_Rate
      REAL Starting_Ambient_Pressure, Ending_Ambient_Pressure
      REAL New_Ambient_Pressure, Segment_Time
      REAL Temp_Helium_Pressure, Temp_Nitrogen_Pressure
      REAL Coefficient_A, Coefficient_B
      REAL SCHREINER_EQUATION !function subprogram
C===============================================================================
C LOCAL ARRAYS
C===============================================================================
      REAL Initial_Helium_Pressure(16), Initial_Nitrogen_Pressure(16)
      REAL Temp_Gas_Loading(16), Allowable_Gas_Loading (16)
C===============================================================================
C GLOBAL CONSTANTS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Water_Vapor_Pressure
      COMMON /Block_8/ Water_Vapor_Pressure
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      INTEGER Mix_Number
      COMMON /Block_9/ Mix_Number
      REAL Barometric_Pressure
      COMMON /Block_18/ Barometric_Pressure
      REAL Gradient_Factor
      COMMON /Block_37/ Gradient_Factor
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Helium_Time_Constant(16)
      COMMON /Block_1A/ Helium_Time_Constant
      REAL Nitrogen_Time_Constant(16)
      COMMON /Block_1B/ Nitrogen_Time_Constant
      REAL Helium_Pressure(16), Nitrogen_Pressure(16) !input
      COMMON /Block_3/ Helium_Pressure, Nitrogen_Pressure
      REAL Fraction_Helium(10), Fraction_Nitrogen(10)
      COMMON /Block_5/ Fraction_Helium, Fraction_Nitrogen
      REAL Coefficient_AHE(16), Coefficient_BHE(16)
      REAL Coefficient_AN2(16), Coefficient_BN2(16)
      COMMON /Block_35/ Coefficient_AHE, Coefficient_BHE,
     * Coefficient_AN2, Coefficient_BN2
C===============================================================================
C CALCULATIONS
C===============================================================================
      New_Ambient_Pressure = Deco_Stop_Depth + Barometric_Pressure
      Starting_Ambient_Pressure = Starting_Depth + Barometric_Pressure
      Initial_Inspired_He_Pressure = (Starting_Ambient_Pressure -
     * Water_Vapor_Pressure)*Fraction_Helium(Mix_Number)
      Initial_Inspired_N2_Pressure = (Starting_Ambient_Pressure -
     * Water_Vapor_Pressure)*Fraction_Nitrogen(Mix_Number)
      Helium_Rate = Rate * Fraction_Helium(Mix_Number)
      Nitrogen_Rate = Rate * Fraction_Nitrogen(Mix_Number)
      DO I = 1,16
      Initial_Helium_Pressure(I) = Helium_Pressure(I)
      Initial_Nitrogen_Pressure(I) = Nitrogen_Pressure(I)
      END DO
665   Ending_Ambient_Pressure = New_Ambient_Pressure
      Segment_Time = (Ending_Ambient_Pressure -
     * Starting_Ambient_Pressure)/Rate
      DO 670 I = 1,16
      Temp_Helium_Pressure = SCHREINER_EQUATION
     * (Initial_Inspired_He_Pressure, Helium_Rate,
     * Segment_Time, Helium_Time_Constant(I),
     * Initial_Helium_Pressure(I))
      Temp_Nitrogen_Pressure = SCHREINER_EQUATION
     * (Initial_Inspired_N2_Pressure, Nitrogen_Rate,
     * Segment_Time, Nitrogen_Time_Constant(I),
     * Initial_Nitrogen_Pressure(I))
      Temp_Gas_Loading(I) = Temp_Helium_Pressure +
     * Temp_Nitrogen_Pressure
      Coefficient_A = (Temp_Helium_Pressure*Coefficient_AHE(I) +
     * Temp_Nitrogen_Pressure*Coefficient_AN2(I))/
     * (Temp_Helium_Pressure+Temp_Nitrogen_Pressure)
      Coefficient_B = (Temp_Helium_Pressure*Coefficient_BHE(I) +
     * Temp_Nitrogen_Pressure*Coefficient_BN2(I))/
     * (Temp_Helium_Pressure+Temp_Nitrogen_Pressure)
      Allowable_Gas_Loading(I) = Ending_Ambient_Pressure *
     * (Gradient_Factor/Coefficient_B - Gradient_Factor + 1.0) +
     * Gradient_Factor*Coefficient_A
670   CONTINUE
      DO 671 I = 1,16
      IF (Temp_Gas_Loading(I) .GT. Allowable_Gas_Loading(I)) THEN
      New_Ambient_Pressure = Ending_Ambient_Pressure + Step_Size
      Deco_Stop_Depth = Deco_Stop_Depth + Step_Size
      GOTO 665
      END IF
671   CONTINUE
C===============================================================================
C END OF SUBROUTINE
C===============================================================================
      RETURN
      END
C===============================================================================
C SUBROUTINE DECOMPRESSION_STOP
C Purpose: This subprogram calculates the required time at each
C decompression stop.
C===============================================================================
      SUBROUTINE DECOMPRESSION_STOP (Deco_Stop_Depth, Step_Size)
      IMPLICIT NONE
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Deco_Stop_Depth, Step_Size !input
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      CHARACTER OS_Command*3
      INTEGER I !loop counter
      INTEGER Last_Segment_Number
      REAL Ambient_Pressure
      REAL Inspired_Helium_Pressure, Inspired_Nitrogen_Pressure
      REAL Last_Run_Time
      REAL Deco_Ceiling_Depth, Next_Stop
      REAL Round_Up_Operation, Temp_Segment_Time, Time_Counter
      REAL Allowable_Gas_Loading
      REAL Coefficient_A, Coefficient_B
      REAL HALDANE_EQUATION !function subprogram
C===============================================================================
C LOCAL ARRAYS
C===============================================================================
      REAL Initial_Helium_Pressure(16)
      REAL Initial_Nitrogen_Pressure(16)
C===============================================================================
C GLOBAL CONSTANTS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Water_Vapor_Pressure
      COMMON /Block_8/ Water_Vapor_Pressure
      REAL Minimum_Deco_Stop_Time
      COMMON /Block_21/ Minimum_Deco_Stop_Time
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      INTEGER Segment_Number
      REAL Run_Time, Segment_Time
      COMMON /Block_2/ Run_Time, Segment_Number, Segment_Time
      REAL Ending_Ambient_Pressure
      COMMON /Block_4/ Ending_Ambient_Pressure
      INTEGER Mix_Number
      COMMON /Block_9/ Mix_Number
      REAL Barometric_Pressure
      COMMON /Block_18/ Barometric_Pressure
      REAL Gradient_Factor
      COMMON /Block_37/ Gradient_Factor
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Helium_Time_Constant(16)
      COMMON /Block_1A/ Helium_Time_Constant
      REAL Nitrogen_Time_Constant(16)
      COMMON /Block_1B/ Nitrogen_Time_Constant
      REAL Helium_Pressure(16), Nitrogen_Pressure(16) !both input
      COMMON /Block_3/ Helium_Pressure, Nitrogen_Pressure !and output
      REAL Fraction_Helium(10), Fraction_Nitrogen(10)
      COMMON /Block_5/ Fraction_Helium, Fraction_Nitrogen
      REAL Coefficient_AHE(16), Coefficient_BHE(16)
      REAL Coefficient_AN2(16), Coefficient_BN2(16)
      COMMON /Block_35/ Coefficient_AHE, Coefficient_BHE,
     * Coefficient_AN2, Coefficient_BN2
C===============================================================================
C CALCULATIONS
C===============================================================================
      OS_Command = 'CLS'
      Last_Run_Time = Run_Time
      Round_Up_Operation = ANINT((Last_Run_Time/Minimum_Deco_Stop_Time)
     * + 0.5) * Minimum_Deco_Stop_Time
      Segment_Time = Round_Up_Operation - Run_Time
      Run_Time = Round_Up_Operation
      Temp_Segment_Time = Segment_Time
      Last_Segment_Number = Segment_Number
      Segment_Number = Last_Segment_Number + 1
      Ambient_Pressure = Deco_Stop_Depth + Barometric_Pressure
      Ending_Ambient_Pressure = Ambient_Pressure
      Next_Stop = Deco_Stop_Depth - Step_Size
      Inspired_Helium_Pressure = (Ambient_Pressure -
     * Water_Vapor_Pressure)*Fraction_Helium(Mix_Number)
      Inspired_Nitrogen_Pressure = (Ambient_Pressure -
     * Water_Vapor_Pressure)*Fraction_Nitrogen(Mix_Number)
C===============================================================================
C Check to make sure that program won't lock up if unable to decompress
C to the next stop. If so, write error message and terminate program.
C===============================================================================
      DO I = 1,16
      IF ((Inspired_Helium_Pressure + Inspired_Nitrogen_Pressure)
     * .GT. 0.0) THEN
      Coefficient_A = (Inspired_Helium_Pressure*Coefficient_AHE(I) +
     * Inspired_Nitrogen_Pressure*Coefficient_AN2(I))/
     * (Inspired_Helium_Pressure + Inspired_Nitrogen_Pressure)
      Coefficient_B = (Inspired_Helium_Pressure*Coefficient_BHE(I) +
     * Inspired_Nitrogen_Pressure*Coefficient_BN2(I))/
     * (Inspired_Helium_Pressure + Inspired_Nitrogen_Pressure)
      Allowable_Gas_Loading = (Next_Stop + Barometric_Pressure) *
     * (Gradient_Factor/Coefficient_B - Gradient_Factor + 1.0) +
     * Gradient_Factor*Coefficient_A
      IF ((Inspired_Helium_Pressure + Inspired_Nitrogen_Pressure)
     * .GT. Allowable_Gas_Loading) THEN
C     CALL SYSTEMQQ (OS_Command)
      WRITE (*,905) Deco_Stop_Depth
      WRITE (*,906)
      WRITE (*,907)
      STOP 'PROGRAM TERMINATED'
      END IF
      END IF
      END DO
700   DO 720 I = 1,16
      Initial_Helium_Pressure(I) = Helium_Pressure(I)
      Initial_Nitrogen_Pressure(I) = Nitrogen_Pressure(I)
      Helium_Pressure(I) = HALDANE_EQUATION
     * (Initial_Helium_Pressure(I), Inspired_Helium_Pressure,
     * Helium_Time_Constant(I), Segment_Time)
      Nitrogen_Pressure(I) = HALDANE_EQUATION
     * (Initial_Nitrogen_Pressure(I), Inspired_Nitrogen_Pressure,
     * Nitrogen_Time_Constant(I), Segment_Time)
720   CONTINUE
      CALL CALC_DECO_CEILING (Deco_Ceiling_Depth)
      IF (Deco_Ceiling_Depth .GT. Next_Stop) THEN
      Segment_Time = Minimum_Deco_Stop_Time
      Time_Counter = Temp_Segment_Time
      Temp_Segment_Time = Time_Counter + Minimum_Deco_Stop_Time
      Last_Run_Time = Run_Time
      Run_Time = Last_Run_Time + Minimum_Deco_Stop_Time
      GOTO 700
      END IF
      Segment_Time = Temp_Segment_Time
C===============================================================================
C FORMAT STATEMENTS - ERROR MESSAGES
C===============================================================================
905   FORMAT ('0ERROR! OFF-GASSING GRADIENT IS TOO SMALL TO DECOMPRESS',
     *1X,'AT THE',F6.1,1X,'STOP')
906   FORMAT ('0REDUCE STEP SIZE OR INCREASE OXYGEN FRACTION')
907   FORMAT (' ')
C===============================================================================
C END OF SUBROUTINE
C===============================================================================
      END
C===============================================================================
C SUBROUTINE GAS_LOADINGS_SURFACE_INTERVAL
C Purpose: This subprogram calculates the gas loading (off-gassing) during
C a surface interval.
C===============================================================================
      SUBROUTINE GAS_LOADINGS_SURFACE_INTERVAL (Surface_Interval_Time)
      IMPLICIT NONE
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Surface_Interval_Time !input
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      INTEGER I !loop counter
      REAL Inspired_Helium_Pressure, Inspired_Nitrogen_Pressure
      REAL Initial_Helium_Pressure, Initial_Nitrogen_Pressure
      REAL HALDANE_EQUATION !function subprogram
C===============================================================================
C GLOBAL CONSTANTS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Water_Vapor_Pressure
      COMMON /Block_8/ Water_Vapor_Pressure
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Barometric_Pressure
      COMMON /Block_18/ Barometric_Pressure
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Helium_Time_Constant(16)
      COMMON /Block_1A/ Helium_Time_Constant
      REAL Nitrogen_Time_Constant(16)
      COMMON /Block_1B/ Nitrogen_Time_Constant
      REAL Helium_Pressure(16), Nitrogen_Pressure(16) !both input
      COMMON /Block_3/ Helium_Pressure, Nitrogen_Pressure !and output
C===============================================================================
C CALCULATIONS
C===============================================================================
      Inspired_Helium_Pressure = 0.0
      Inspired_Nitrogen_Pressure = (Barometric_Pressure -
     * Water_Vapor_Pressure)*0.79
      DO I = 1,16
      Initial_Helium_Pressure = Helium_Pressure(I)
      Initial_Nitrogen_Pressure = Nitrogen_Pressure(I)
      Helium_Pressure(I) = HALDANE_EQUATION
     * (Initial_Helium_Pressure, Inspired_Helium_Pressure,
     * Helium_Time_Constant(I), Surface_Interval_Time)
      Nitrogen_Pressure(I) = HALDANE_EQUATION
     * (Initial_Nitrogen_Pressure, Inspired_Nitrogen_Pressure,
     * Nitrogen_Time_Constant(I), Surface_Interval_Time)
      END DO
C===============================================================================
C END OF SUBROUTINE
C===============================================================================
      RETURN
      END
C===============================================================================
C SUBROUTINE CALC_BAROMETRIC_PRESSURE
C Purpose: This sub calculates barometric pressure at altitude based on the
C publication "U.S. Standard Atmosphere, 1976", U.S. Government Printing
C Office, Washington, D.C. The source for this code is a Fortran 90 program
C written by Ralph L. Carmichael (retired NASA researcher) and endorsed by
C the National Geophysical Data Center of the National Oceanic and
C Atmospheric Administration. It is available for download free from
C Public Domain Aeronautical Software at: http://www.pdas.com/atmos.htm
C===============================================================================
      SUBROUTINE CALC_BAROMETRIC_PRESSURE (Altitude)
      IMPLICIT NONE
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Altitude !input
C===============================================================================
C LOCAL CONSTANTS
C===============================================================================
      REAL Radius_of_Earth, Acceleration_of_Gravity
      REAL Molecular_weight_of_Air, Gas_Constant_R
      REAL Temp_at_Sea_Level, Temp_Gradient
      REAL Pressure_at_Sea_Level_Fsw, Pressure_at_Sea_Level_Msw
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      REAL Pressure_at_Sea_Level, GMR_Factor
      REAL Altitude_Feet, Altitude_Meters
      REAL Altitude_Kilometers, Geopotential_Altitude
      REAL Temp_at_Geopotential_Altitude
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      LOGICAL Units_Equal_Fsw, Units_Equal_Msw
      COMMON /Block_15/ Units_Equal_Fsw, Units_Equal_Msw
      REAL Barometric_Pressure !output
      COMMON /Block_18/ Barometric_Pressure
C===============================================================================
C CALCULATIONS
C===============================================================================
      Radius_of_Earth = 6369.0 !kilometers
      Acceleration_of_Gravity = 9.80665 !meters/second^2
      Molecular_weight_of_Air = 28.9644 !mols
      Gas_Constant_R = 8.31432 !Joules/mol*deg Kelvin
      Temp_at_Sea_Level = 288.15 !degrees Kelvin
      Pressure_at_Sea_Level_Fsw = 33.0 !feet of seawater based on 101325 Pa
      !at sea level (Standard Atmosphere)
      Pressure_at_Sea_Level_Msw = 10.0 !meters of seawater based on 100000 Pa
      !at sea level (European System)
      Temp_Gradient = -6.5 !Change in Temp deg Kelvin with
      !change in geopotential altitude,
      !valid for first layer of atmosphere
      !up to 11 kilometers or 36,000 feet
      GMR_Factor = Acceleration_of_Gravity *
     * Molecular_weight_of_Air / Gas_Constant_R
      IF (Units_Equal_Fsw) THEN
      Altitude_Feet = Altitude
      Altitude_Kilometers = Altitude_Feet / 3280.839895
      Pressure_at_Sea_Level = Pressure_at_Sea_Level_Fsw
      END IF
      IF (Units_Equal_Msw) THEN
      Altitude_Meters = Altitude
      Altitude_Kilometers = Altitude_Meters / 1000.0
      Pressure_at_Sea_Level = Pressure_at_Sea_Level_Msw
      END IF
      Geopotential_Altitude = (Altitude_Kilometers * Radius_of_Earth) /
     * (Altitude_Kilometers + Radius_of_Earth)
      Temp_at_Geopotential_Altitude = Temp_at_Sea_Level
     * + Temp_Gradient * Geopotential_Altitude
      Barometric_Pressure = Pressure_at_Sea_Level *
     * EXP(ALOG(Temp_at_Sea_Level / Temp_at_Geopotential_Altitude) *
     * GMR_Factor / Temp_Gradient)
C===============================================================================
C END OF SUBROUTINE
C===============================================================================
      RETURN
      END
C===============================================================================
C SUBROUTINE ALTITUDE_DIVE_ALGORITHM
C Purpose: This subprogram updates gas loadings (as required) based on
C whether or not diver is acclimatized at altitude or makes an ascent to
C altitude before the dive.
C===============================================================================
      SUBROUTINE ALTITUDE_DIVE_SUBPROGRAM
      IMPLICIT NONE
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      CHARACTER Diver_Acclimatized_at_Altitude*3, OS_Command*3
      INTEGER I !loop counter
      LOGICAL Diver_Acclimatized
      REAL Starting_Acclimatized_Altitude
      REAL Ascent_to_Altitude_Hours, Hours_at_Altitude_Before_Dive
      REAL Ascent_to_Altitude_Time, Time_at_Altitude_Before_Dive
      REAL Starting_Ambient_Pressure, Ending_Ambient_Pressure
      REAL Initial_Inspired_N2_Pressure, Rate, Nitrogen_Rate
      REAL Inspired_Nitrogen_Pressure, Initial_Nitrogen_Pressure
      REAL HALDANE_EQUATION !function subprogram
      REAL SCHREINER_EQUATION !function subprogram
C===============================================================================
C GLOBAL CONSTANTS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Water_Vapor_Pressure
      COMMON /Block_8/ Water_Vapor_Pressure
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      LOGICAL Units_Equal_Fsw, Units_Equal_Msw
      COMMON /Block_15/ Units_Equal_Fsw, Units_Equal_Msw
      REAL Units_Factor
      COMMON /Block_16/ Units_Factor
      REAL Barometric_Pressure
      COMMON /Block_18/ Barometric_Pressure
      REAL Altitude_of_Dive
      COMMON /Block_33/ Altitude_of_Dive
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Nitrogen_Time_Constant(16)
      COMMON /Block_1B/ Nitrogen_Time_Constant
      REAL Helium_Pressure(16), Nitrogen_Pressure(16) !both input
      COMMON /Block_3/ Helium_Pressure, Nitrogen_Pressure !and output
C===============================================================================
C NAMELIST FOR PROGRAM SETTINGS (READ IN FROM ASCII TEXT FILE)
C===============================================================================
      NAMELIST /Altitude_Dive_Settings/ Altitude_of_Dive,
     * Diver_Acclimatized_at_Altitude,
     * Starting_Acclimatized_Altitude, Ascent_to_Altitude_Hours,
     * Hours_at_Altitude_Before_Dive
C===============================================================================
C CALCULATIONS
C===============================================================================
C      OS_Command = 'CLS'
      OPEN (UNIT = 14, FILE = 'ALTITUDE.SET', STATUS = 'UNKNOWN',
     * ACCESS = 'SEQUENTIAL', FORM = 'FORMATTED')
      READ (14,Altitude_Dive_Settings)
      IF ((Units_Equal_Fsw) .AND. (Altitude_of_Dive .GT. 30000.0)) THEN
C     CALL SYSTEMQQ (OS_Command)
      WRITE (*,900)
      WRITE (*,901)
      STOP 'PROGRAM TERMINATED'
      END IF
      IF ((Units_Equal_Msw) .AND. (Altitude_of_Dive .GT. 9144.0)) THEN
C     CALL SYSTEMQQ (OS_Command)
      WRITE (*,900)
      WRITE (*,901)
      STOP 'PROGRAM TERMINATED'
      END IF
      IF ((Diver_Acclimatized_at_Altitude .EQ. 'YES') .OR.
     * (Diver_Acclimatized_at_Altitude .EQ. 'yes')) THEN
      Diver_Acclimatized = (.TRUE.)
      ELSE IF ((Diver_Acclimatized_at_Altitude .EQ. 'NO') .OR.
     * (Diver_Acclimatized_at_Altitude .EQ. 'no')) THEN
      Diver_Acclimatized = (.FALSE.)
      ELSE
C     CALL SYSTEMQQ (OS_Command)
      WRITE (*,902)
      WRITE (*,901)
      STOP 'PROGRAM TERMINATED'
      END IF
      Ascent_to_Altitude_Time = Ascent_to_Altitude_Hours * 60.0
      Time_at_Altitude_Before_Dive = Hours_at_Altitude_Before_Dive*60.0
      IF (Diver_Acclimatized) THEN
      CALL CALC_BAROMETRIC_PRESSURE (Altitude_of_Dive)
      WRITE (*,802) Altitude_of_Dive, Barometric_Pressure
      DO I = 1,16
      Helium_Pressure(I) = 0.0
      Nitrogen_Pressure(I) = (Barometric_Pressure -
     * Water_Vapor_Pressure)*0.79
      END DO
      ELSE
      IF ((Starting_Acclimatized_Altitude .GE. Altitude_of_Dive)
     * .OR. (Starting_Acclimatized_Altitude .LT. 0.0)) THEN
C     CALL SYSTEMQQ (OS_Command)
      WRITE (*,903)
      WRITE (*,904)
      WRITE (*,901)
      STOP 'PROGRAM TERMINATED'
      END IF
      CALL CALC_BAROMETRIC_PRESSURE (Starting_Acclimatized_Altitude)
      Starting_Ambient_Pressure = Barometric_Pressure
      DO I = 1,16
      Helium_Pressure(I) = 0.0
      Nitrogen_Pressure(I) = (Barometric_Pressure -
     * Water_Vapor_Pressure)*0.79
      END DO
      CALL CALC_BAROMETRIC_PRESSURE (Altitude_of_Dive)
      WRITE (*,802) Altitude_of_Dive, Barometric_Pressure
      Ending_Ambient_Pressure = Barometric_Pressure
      Initial_Inspired_N2_Pressure = (Starting_Ambient_Pressure
     * - Water_Vapor_Pressure)*0.79
      Rate = (Ending_Ambient_Pressure - Starting_Ambient_Pressure)
     * / Ascent_to_Altitude_Time
      Nitrogen_Rate = Rate*0.79
      DO I = 1,16
      Initial_Nitrogen_Pressure = Nitrogen_Pressure(I)
      Nitrogen_Pressure(I) = SCHREINER_EQUATION
     * (Initial_Inspired_N2_Pressure, Nitrogen_Rate,
     * Ascent_to_Altitude_Time, Nitrogen_Time_Constant(I),
     * Initial_Nitrogen_Pressure)
      END DO
      Inspired_Nitrogen_Pressure = (Barometric_Pressure -
     * Water_Vapor_Pressure)*0.79
      DO I = 1,16
      Initial_Nitrogen_Pressure = Nitrogen_Pressure(I)
      Nitrogen_Pressure(I) = HALDANE_EQUATION
     * (Initial_Nitrogen_Pressure, Inspired_Nitrogen_Pressure,
     * Nitrogen_Time_Constant(I), Time_at_Altitude_Before_Dive)
      END DO
      END IF
      CLOSE (UNIT = 14, STATUS = 'KEEP')
      RETURN
C===============================================================================
C FORMAT STATEMENTS - PROGRAM OUTPUT
C===============================================================================
802   FORMAT ('0ALTITUDE = ',1X,F7.1,4X,'BAROMETRIC PRESSURE = ',
     *F6.3)
C===============================================================================
C FORMAT STATEMENTS - ERROR MESSAGES
C===============================================================================
900   FORMAT ('0ERROR! ALTITUDE OF DIVE HIGHER THAN MOUNT EVEREST')
901   FORMAT (' ')
902   FORMAT ('0ERROR! DIVER ACCLIMATIZED AT ALTITUDE',
     *1X,'MUST BE YES OR NO')
903   FORMAT ('0ERROR! STARTING ACCLIMATIZED ALTITUDE MUST BE LESS',
     *1X,'THAN ALTITUDE OF DIVE')
904   FORMAT (' AND GREATER THAN OR EQUAL TO ZERO')
C===============================================================================
C END OF SUBROUTINE
C===============================================================================
      END
C===============================================================================
C SUBROUTINE DIVEDATA_ASCENT_DESCENT
C===============================================================================
      SUBROUTINE DIVEDATA_ASCENT_DESCENT (Starting_Depth, Ending_Depth,
     * Rate, Respiratory_Minute_Volume)
      IMPLICIT NONE
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Starting_Depth, Ending_Depth, Rate, Respiratory_Minute_Volume
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      INTEGER I !loop counter
      REAL PARATE, PATAO, PATAF, SEGVOL
      REAL TEMPRV, MAXATA, MINATA, MAXPO2
      REAL SUMCNS, TMPCNS
      REAL OTU, MAXD, ENDN2, ENDNO2
      REAL MINPO2, LOWPO2, O2TIME, IPO2, FPO2, CNSTMP, OTUTMP
C===============================================================================
C LOCAL ARRAYS
C===============================================================================
      REAL OTIME(10), SEGPO2(10)
      REAL PO2O(10), PO2F(10), TLIMO(10)
      REAL SLPCON(10), CNS(10)
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      INTEGER Segment_Number
      REAL Run_Time, Segment_Time
      COMMON /Block_2/ Run_Time, Segment_Number, Segment_Time
      INTEGER Mix_Number
      COMMON /Block_9/ Mix_Number
      REAL Units_Factor
      COMMON /Block_16/ Units_Factor
      REAL Barometric_Pressure
      COMMON /Block_18/ Barometric_Pressure
      REAL Running_CNS, Running_OTU
      COMMON /Block_32/ Running_CNS, Running_OTU
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Fraction_Helium(10), Fraction_Nitrogen(10)
      COMMON /Block_5/ Fraction_Helium, Fraction_Nitrogen
      REAL PO2LO(10), PO2HI(10), LIMSLP(10), LIMINT(10)
      COMMON /Block_29/ PO2LO, PO2HI, LIMSLP, LIMINT
      REAL Fraction_Oxygen(10)
      COMMON /Block_30/ Fraction_Oxygen
      REAL Running_Gas_Volume(10)
      COMMON /Block_31/ Running_Gas_Volume
C===============================================================================
C CALCULATIONS
C===============================================================================
      SUMCNS = 0.0
      OTU = 0.0
      PARATE = Rate/Units_Factor
      PATAO = (Starting_Depth + Barometric_Pressure )/Units_Factor
      PATAF = (Ending_Depth + Barometric_Pressure)/Units_Factor
      SEGVOL = Respiratory_Minute_Volume*(PATAO*Segment_Time + 0.5*
     * PARATE*Segment_Time**2)
      TEMPRV = Running_Gas_Volume(Mix_Number)
      Running_Gas_Volume(Mix_Number) = TEMPRV + SEGVOL
      MAXATA = MAX(PATAO, PATAF)
      MINATA = MIN(PATAO, PATAF)
      MAXPO2 = MAXATA * Fraction_Oxygen(Mix_Number)
      MINPO2 = MINATA * Fraction_Oxygen(Mix_Number)
      MAXD = MAX(Starting_Depth, Ending_Depth)
      ENDN2 = (Fraction_Nitrogen(Mix_Number)*(MAXD +
     * Barometric_Pressure)/0.79) - Barometric_Pressure
      ENDNO2 = Fraction_Nitrogen(Mix_Number)*(MAXD +
     * Barometric_Pressure)+ Fraction_Oxygen(Mix_Number)*
     * (MAXD + Barometric_Pressure)-Barometric_Pressure
      IF (MAXPO2 .LE. 0.5) GOTO 50
      IF (MINPO2 .LT. 0.5) THEN
      LOWPO2 = 0.5
      ELSE
      LOWPO2 = MINPO2
      END IF
      O2TIME = Segment_Time*(MAXPO2 - LOWPO2)/(MAXPO2 - MINPO2)
      IF (MAXPO2 .GT. 1.82) THEN
      SUMCNS = 2.0
      OTU = 3.0/11.0*O2TIME/(MAXPO2-LOWPO2)*(((MAXPO2-0.5)/0.5)
     * **(11.0/6.0) - ((LOWPO2-0.5)/0.5)**(11.0/6.0))
      GOTO 50
      END IF
      DO 10 I = 1,10
      IF ((MAXPO2 .GT. PO2LO(I)) .AND. (LOWPO2 .LE. PO2HI(I))) THEN
      IF ((MAXPO2 .GE. PO2HI(I)) .AND. (LOWPO2 .LT. PO2LO(I))) THEN
      IF (Starting_Depth .GT. Ending_Depth) THEN
      PO2O(I) = PO2HI(I)
      PO2F(I) = PO2LO(I)
      ELSE
      PO2O(I) = PO2LO(I)
      PO2F(I) = PO2HI(I)
      END IF
      SEGPO2(I) = PO2F(I) - PO2O(I)
      ELSE IF ((MAXPO2 .LT. PO2HI(I)) .AND. (LOWPO2 .LE. PO2LO(I))) THEN
      IF (Starting_Depth .GT. Ending_Depth) THEN
      PO2O(I) = MAXPO2
      PO2F(I) = PO2LO(I)
      ELSE
      PO2O(I) = PO2LO(I)
      PO2F(I) = MAXPO2
      END IF
      SEGPO2(I) = PO2F(I) - PO2O(I)
      ELSE IF ((LOWPO2 .GT. PO2LO(I)) .AND. (MAXPO2 .GE. PO2HI(I))) THEN
      IF (Starting_Depth .GT. Ending_Depth) THEN
      PO2O(I) = PO2HI(I)
      PO2F(I) = LOWPO2
      ELSE
      PO2O(I) = LOWPO2
      PO2F(I) = PO2HI(I)
      END IF
      SEGPO2(I) = PO2F(I) - PO2O(I)
      ELSE
      IF (Starting_Depth .GT. Ending_Depth) THEN
      PO2O(I) = MAXPO2
      PO2F(I) = LOWPO2
      ELSE
      PO2O(I) = LOWPO2
      PO2F(I) = MAXPO2
      END IF
      SEGPO2(I) = PO2F(I) - PO2O(I)
      END IF
      OTIME(I) = O2TIME*ABS(SEGPO2(I))/(MAXPO2 - LOWPO2)
      ELSE
      OTIME(I) = 0.0
      END IF
10    CONTINUE
      DO 20 I = 1,10
      IF (OTIME(I) .EQ. 0.0) THEN
      CNS(I) = 0.0
      GOTO 20
      ELSE
      TLIMO(I) = LIMSLP(I)*PO2O(I) + LIMINT(I)
      SLPCON(I) = LIMSLP(I)*(SEGPO2(I)/OTIME(I))
      CNS(I) = 1.0/SLPCON(I)*LOG(ABS(TLIMO(I) + SLPCON(I)*OTIME(I))) -
     * 1.0/SLPCON(I)*LOG(ABS(TLIMO(I)))
      END IF
20    CONTINUE
      DO 30 I = 1, 10
      TMPCNS = SUMCNS
      SUMCNS = TMPCNS + CNS(I)
30    CONTINUE
      IF (Starting_Depth .GT. Ending_Depth) THEN
      IPO2 = MAXPO2
      FPO2 = LOWPO2
      ELSE
      IPO2 = LOWPO2
      FPO2 = MAXPO2
      END IF
      OTU = 3.0/11.0*O2TIME/(FPO2-IPO2)*(((FPO2-0.5)/0.5)**(11.0/6.0)
     * - ((IPO2-0.5)/0.5)**(11.0/6.0))
50    CNSTMP = Running_CNS
      Running_CNS = CNSTMP + SUMCNS
      OTUTMP = Running_OTU
      Running_OTU = OTUTMP + OTU
      WRITE (13,100) Segment_Number, Segment_Time, Run_Time, Mix_Number,
     * Respiratory_Minute_Volume, SEGVOL, MAXD,
     * MAXPO2, SUMCNS, OTU, ENDN2, ENDNO2
100   FORMAT (I3,3X,F5.1,1X,F6.1,1X,'|',3X,I2,3X,'|',F5.2,1X,F7.1,1X,
     * F6.0,2X,F4.2,1X,2P,F7.1,'%',0P,F7.1,2X,F6.0,2X,F6.0)
      IF (MAXPO2 .GT. 1.6061) THEN
      CALL PO2_WARNING (Segment_Number)
      END IF
      IF (MAXPO2 .GT. 1.82) THEN
      CALL EXCEPTIONAL_PO2_WARNING (Segment_Number)
      END IF
      RETURN
      END
C===============================================================================
C SUBROUTINE DIVEDATA_CONSTANT_DEPTH
C===============================================================================
      SUBROUTINE DIVEDATA_CONSTANT_DEPTH (Depth,
     * Respiratory_Minute_Volume)
      IMPLICIT NONE
C===============================================================================
C ARGUMENTS
C===============================================================================
      REAL Depth, Respiratory_Minute_Volume
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      INTEGER I !loop counter
      REAL Ambient_Pressure_ATA, Segment_Volume, Temp_Running_Volume
      REAL SUMCNS, PO2, TLIM, OTU, MAXD, MAXPO2
      REAL ENDN2, ENDNO2, CNSTMP, OTUTMP
C===============================================================================
C GLOBAL VARIABLES IN NAMED COMMON BLOCKS
C===============================================================================
      INTEGER Segment_Number
      REAL Run_Time, Segment_Time
      COMMON /Block_2/ Run_Time, Segment_Number, Segment_Time
      INTEGER Mix_Number
      COMMON /Block_9/ Mix_Number
      REAL Units_Factor
      COMMON /Block_16/ Units_Factor
      REAL Barometric_Pressure
      COMMON /Block_18/ Barometric_Pressure
      REAL Running_CNS, Running_OTU
      COMMON /Block_32/ Running_CNS, Running_OTU
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL Fraction_Helium(10), Fraction_Nitrogen(10)
      COMMON /Block_5/ Fraction_Helium, Fraction_Nitrogen
      REAL PO2LO(10), PO2HI(10), LIMSLP(10), LIMINT(10)
      COMMON /Block_29/ PO2LO, PO2HI, LIMSLP, LIMINT
      REAL Fraction_Oxygen(10)
      COMMON /Block_30/ Fraction_Oxygen
      REAL Running_Gas_Volume(10)
      COMMON /Block_31/ Running_Gas_Volume
C===============================================================================
C CALCULATIONS
C===============================================================================
      SUMCNS = 0.0
      OTU = 0.0
      Ambient_Pressure_ATA = (Depth + Barometric_Pressure)/Units_Factor
      Segment_Volume = Respiratory_Minute_Volume*Ambient_Pressure_ATA*
     * Segment_Time
      Temp_Running_Volume = Running_Gas_Volume(Mix_Number)
      Running_Gas_Volume(Mix_Number) = Temp_Running_Volume +
     * Segment_Volume
      PO2 = Ambient_Pressure_ATA * Fraction_Oxygen(Mix_Number)
      MAXPO2 = PO2
      MAXD = Depth
      ENDN2 = (Fraction_Nitrogen(Mix_Number)*(Depth +
     * Barometric_Pressure)/0.79) - Barometric_Pressure
      ENDNO2 = Fraction_Nitrogen(Mix_Number)*(Depth +
     * Barometric_Pressure)+Fraction_Oxygen(Mix_Number)*
     * (Depth+Barometric_Pressure)-Barometric_Pressure
      IF (PO2 .LE. 0.5) GOTO 50
      IF (PO2 .GT. 1.82) THEN
      SUMCNS = 2.0
      GOTO 30
      END IF
      DO 10 I = 1,10
      IF ((PO2 .GT. PO2LO(I)) .AND. (PO2 .LE. PO2HI(I))) THEN
      TLIM = LIMSLP(I)*PO2 + LIMINT(I)
      GOTO 20
      END IF
10    CONTINUE
20    SUMCNS = Segment_Time/TLIM
30    OTU = Segment_Time*((0.5/(PO2-0.5))**(-5.0/6.0))
50    CNSTMP = Running_CNS
      Running_CNS = CNSTMP + SUMCNS
      OTUTMP = Running_OTU
      Running_OTU = OTUTMP + OTU
      WRITE (13,100) Segment_Number, Segment_Time, Run_Time, Mix_Number,
     * Respiratory_Minute_Volume, Segment_Volume, MAXD,
     * MAXPO2, SUMCNS, OTU, ENDN2, ENDNO2
100   FORMAT (I3,3X,F5.1,1X,F6.1,1X,'|',3X,I2,3X,'|',F5.2,1X,F7.1,1X,
     * F6.0,2X,F4.2,1X,2P,F7.1,'%',0P,F7.1,2X,F6.0,2X,F6.0)
      IF (MAXPO2 .GT. 1.6061) THEN
      CALL PO2_WARNING (Segment_Number)
      END IF
      IF (MAXPO2 .GT. 1.82) THEN
      CALL EXCEPTIONAL_PO2_WARNING (Segment_Number)
      END IF
      RETURN
      END
C===============================================================================
C SUBROUTINE PO2_WARNING
C===============================================================================
      SUBROUTINE PO2_WARNING (Segment_Number)
      IMPLICIT NONE
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      INTEGER Segment_Number
C===============================================================================
C WRITE WARNING MESSAGE
C===============================================================================
      WRITE (13,5)
      WRITE (13,10) Segment_Number
      WRITE (13,5)
C===============================================================================
C FORMAT STATEMENTS
C===============================================================================
5     FORMAT (' ')
10    FORMAT ('WARNING - SEGMENT #',I3,': PO2 EXCEEDS TECHNICAL',1X,
     * 'DIVING LIMITS')
      RETURN
      END
C===============================================================================
C SUBROUTINE EXCEPTIONAL_PO2_WARNING
C===============================================================================
      SUBROUTINE EXCEPTIONAL_PO2_WARNING (Segment_Number)
      IMPLICIT NONE
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
      INTEGER Segment_Number
C===============================================================================
C WRITE WARNING MESSAGE
C===============================================================================
      WRITE (13,5)
      WRITE (13,10) Segment_Number
      WRITE (13,5)
C===============================================================================
C FORMAT STATEMENTS
C===============================================================================
5     FORMAT (' ')
10    FORMAT ('WARNING - SEGMENT #',I3,': PO2 EXCEPTIONAL EXPOSURE',
     * 1X,'- OUT OF RANGE')
      RETURN
      END
C===============================================================================
C BLOCK DATA SUBPROGRAM CNS_LIMITS
C===============================================================================
      BLOCK DATA CNS_LIMITS
      IMPLICIT NONE
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL PO2LO(10), PO2HI(10), LIMSLP(10), LIMINT(10)
      COMMON /Block_29/ PO2LO, PO2HI, LIMSLP, LIMINT
C===============================================================================
C ASSIGN VALUES TO ARRAYS
C===============================================================================
      DATA PO2LO(1)/0.5/,PO2LO(2)/0.6/,PO2LO(3)/0.7/,PO2LO(4)/0.8/,
     * PO2LO(5)/0.9/,PO2LO(6)/1.1/,PO2LO(7)/1.5/,
     * PO2LO(8)/1.6061/,PO2LO(9)/1.62/,PO2LO(10)/1.74/
      DATA PO2HI(1)/0.6/,PO2HI(2)/0.7/,PO2HI(3)/0.8/,PO2HI(4)/0.9/,
     * PO2HI(5)/1.1/,PO2HI(6)/1.5/,PO2HI(7)/1.6061/,
     * PO2HI(8)/1.62/,PO2HI(9)/1.74/,PO2HI(10)/1.82/
      DATA LIMSLP(1)/-1800.0/,LIMSLP(2)/-1500.0/,LIMSLP(3)/-1200.0/,
     * LIMSLP(4)/-900.0/,LIMSLP(5)/-600.0/,LIMSLP(6)/-300.0/,
     * LIMSLP(7)/-750.0/,LIMSLP(8)/-1250.0/,LIMSLP(9)/-125.0/,
     * LIMSLP(10)/-50.0/
      DATA LIMINT(1)/1800.0/,LIMINT(2)/1620.0/,LIMINT(3)/1410.0/,
     * LIMINT(4)/1170.0/,LIMINT(5)/900.0/,LIMINT(6)/570.0/,
     * LIMINT(7)/1245.0/,LIMINT(8)/2045.0/,LIMINT(9)/222.5/,
     * LIMINT(10)/92.0/
      END
C===============================================================================
C BLOCK DATA SUBPROGRAM M_VALUE_COEFFICIENTS
C===============================================================================
      BLOCK DATA M_VALUE_COEFFICIENTS
      IMPLICIT NONE
C===============================================================================
C GLOBAL ARRAYS IN NAMED COMMON BLOCKS
C===============================================================================
      REAL AHE(16), BHE(16), AN2(16), BN2(16)
      COMMON /Block_34/ AHE, BHE, AN2, BN2
C===============================================================================
C ASSIGN VALUES TO ARRAYS
C===============================================================================
      DATA AHE(1)/16.189/,AHE(2)/13.830/,AHE(3)/11.919/,AHE(4)/10.458/,
     * AHE(5)/9.220/,AHE(6)/8.205/,AHE(7)/7.305/,AHE(8)/6.502/,
     * AHE(9)/5.950/,AHE(10)/5.545/,AHE(11)/5.333/,
     * AHE(12)/5.189/,AHE(13)/5.181/,AHE(14)/5.176/,
     * AHE(15)/5.172/,AHE(16)/5.119/
      DATA BHE(1)/0.4770/,BHE(2)/0.5747/,BHE(3)/0.6527/,BHE(4)/0.7223/,
     * BHE(5)/0.7582/,BHE(6)/0.7957/,BHE(7)/0.8279/,BHE(8)/0.8553/,
     * BHE(9)/0.8757/,BHE(10)/0.8903/,BHE(11)/0.8997/,
     * BHE(12)/0.9073/,BHE(13)/0.9122/,BHE(14)/0.9171/,
     * BHE(15)/0.9217/,BHE(16)/0.9267/
      DATA AN2(1)/11.696/,AN2(2)/10.000/,AN2(3)/8.618/,AN2(4)/7.562/,
     * AN2(5)/6.667/,AN2(6)/5.600/,AN2(7)/4.947/,AN2(8)/4.500/,
     * AN2(9)/4.187/,AN2(10)/3.798/,AN2(11)/3.497/,
     * AN2(12)/3.223/,AN2(13)/2.850/,AN2(14)/2.737/,
     * AN2(15)/2.523/,AN2(16)/2.327/
      DATA BN2(1)/0.5578/,BN2(2)/0.6514/,BN2(3)/0.7222/,BN2(4)/0.7825/,
     * BN2(5)/0.8126/,BN2(6)/0.8434/,BN2(7)/0.8693/,BN2(8)/0.8910/,
     * BN2(9)/0.9092/,BN2(10)/0.9222/,BN2(11)/0.9319/,
     * BN2(12)/0.9403/,BN2(13)/0.9477/,BN2(14)/0.9544/,
     * BN2(15)/0.9602/,BN2(16)/0.9653/
      END
C===============================================================================
C SUBROUTINE CLOCK
C Purpose: This subprogram retrieves clock information from the Microsoft
C operating system so that date and time stamp can be included on program
C output.
C===============================================================================
C     SUBROUTINE CLOCK (Year, Month, Day, Clock_Hour, Minute, M)
C     IMPLICIT NONE
C===============================================================================
C ARGUMENTS
C===============================================================================
C     CHARACTER M*1 !output
C     INTEGER*2 Month, Day, Year !output
C     INTEGER*2 Minute, Clock_Hour !output
C===============================================================================
C LOCAL VARIABLES
C===============================================================================
C     INTEGER*2 Hour, Second, Hundredth
C===============================================================================
C CALCULATIONS
C===============================================================================
C     CALL GETDAT (Year, Month, Day) !Microsoft run-time
C     CALL GETTIM (Hour, Minute, Second, Hundredth) !subroutines
C     IF (Hour .GT. 12) THEN
C     Clock_Hour = Hour - 12
C     M = 'p'
C     ELSE
C     Clock_Hour = Hour
C     M = 'a'
C     ENDIF
C===============================================================================
C END OF SUBROUTINE
C===============================================================================
C     RETURN
C     END

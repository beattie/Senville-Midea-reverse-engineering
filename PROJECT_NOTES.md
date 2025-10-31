# Senville Mini-Split Reverse Engineering - Project Notes

## Project Status: ✅ COMPLETE & WORKING

**Date:** 2025-10-30

## What Works

✅ **Full local control** of Senville mini-split (no cloud needed)
✅ **Status checking** with 3 verbosity levels
✅ **Temperature control** in Celsius or Fahrenheit
✅ **Mode control** (auto/cool/heat/dry/fan)
✅ **Fan speed control** (20/40/60/80/102)
✅ **Swing control** (vertical/horizontal oscillation)
✅ **Command-line tools** that work from any directory

## Device Information

- **Model:** Senville mini-split with OSK105 WiFi adapter
- **IP Address:** 192.168.254.183
- **Device ID:** 149533581404890
- **MAC Address:** B8:8C:29:60:97:8A
- **Protocol:** Midea V3 (same as Midea, Klimaire, Comfee, etc.)

## Key Files

### Commands (in ~/bin)
- `senville-status` - Check AC status
- `senville` - Quick control (simple)
- `senville-control` - Full control (all features)

### Python Scripts (in ~/senville)
- `status.py` - Status checker (3 verbosity levels)
- `control_simple.py` - Basic control
- `control_full.py` - Full control with swing/fan
- `discover.py` - Device discovery

### Configuration
- `.env` - **Contains your credentials** (token, key, IP)
- `.env.example` - Template

### Documentation
- `README.md` - Complete project documentation
- `QUICK_REFERENCE.md` - Quick command reference
- `senville-protocol-documentation.md` - Protocol specs
- `senville-control-guide.md` - Detailed usage guide
- `PROJECT_NOTES.md` - This file

## How to Resume This Project

### In a New Claude Code Chat

Just say:
```
I have a Senville mini-split control project in ~/senville.
Can you help me add [feature]?
```

Or:
```
Resume my Senville AC reverse engineering project in ~/senville
```

### What Claude Code Will See

- All Python scripts
- All documentation
- Git history (shows what was done)
- `.env` file with credentials
- Working command-line tools

## Potential Next Steps / Features to Add

### 1. **Automation & Scheduling**
- Create cron jobs for scheduled temperature changes
- Morning/evening auto-adjustments
- Temperature based on weather

### 2. **Home Assistant Integration**
- Direct integration using existing libraries
- Custom component using our scripts
- Dashboard cards

### 3. **Advanced Protocol Features**
- Eco mode control
- Turbo mode
- Sleep mode
- Timer functions
- Fixed fan angle positions (if protocol supports)

### 4. **UART Direct Control**
- Bypass WiFi entirely
- Direct serial connection to AC unit
- Custom ESP32/ESP8266 dongle
- Fully offline control

### 5. **Monitoring & Logging**
- Temperature logging to database
- Energy usage tracking (if protocol supports)
- Historical data graphs
- Alert on errors

### 6. **Mobile/Web Interface**
- Simple web dashboard
- RESTful API wrapper
- Mobile app (using existing Python backend)

### 7. **Multiple Unit Support**
- Control multiple Senville units
- Zone management
- Synchronized control

### 8. **Voice Control**
- Alexa/Google Home integration
- Custom voice commands

## Technical Details

### Authentication Method Used
- **V3 Protocol** with token/key
- Extracted using `msmart-ng discover` without cloud credentials
- Local network only (UDP discovery on port 6445, TCP control on port 6444)

### Libraries Used
- `midea-beautiful-air` - Main control library
- `msmart-ng` - Discovery and protocol
- `scapy` - Packet analysis (for WiFi capture tools)
- `python-dotenv` - Environment configuration

### Virtual Environment
Location: `~/senville/venv/`
Python: 3.11.2

Activate: `source ~/senville/venv/bin/activate`

### Git Repository
Initialized with full project history.

View log:
```bash
cd ~/senville
git log
```

## Known Limitations

1. **Fixed fan angle positions** - "Direct" button functionality not exposed in protocol
2. **Cloud authentication** - Senville app uses different backend than standard Midea apps
3. **WiFi capture** - Phone app communicates via cloud, not direct to device (local control works though)
4. **Some advanced features** - May not be exposed in the protocol libraries

## Troubleshooting

### If Commands Don't Work
1. Check device is online: `ping 192.168.254.183`
2. Verify credentials in `.env` file
3. Check virtual environment: `source ~/senville/venv/bin/activate`

### If Device IP Changes
1. Find new IP: `nmap -p 6444 --open 192.168.254.0/24`
2. Update `.env` file: `SENVILLE_IP=NEW_IP`
3. Or set DHCP reservation in router

### Re-discover Device
```bash
cd ~/senville
source venv/bin/activate
msmart-ng discover 192.168.254.183
```

## Resources

### GitHub Projects Referenced
- https://github.com/nbogojevic/midea-beautiful-air
- https://github.com/mac-zhou/midea-ac-py
- https://github.com/dudanov/MideaUART
- https://github.com/reneklootwijk/node-mideahvac

### Protocol Information
- Midea protocol uses 9600 baud UART
- WiFi dongle (OSK105) bridges WiFi to UART
- V3 protocol requires token/key authentication
- Compatible with many rebranded Midea units

## Session Summary

**What we did in this session:**
1. ✅ Researched Senville/Midea protocol
2. ✅ Found device on network
3. ✅ Extracted credentials without cloud login
4. ✅ Created Python control scripts
5. ✅ Added Fahrenheit support
6. ✅ Added fan/swing controls
7. ✅ Created command-line tools
8. ✅ Added multiple verbosity levels
9. ✅ Documented everything
10. ✅ Set up git repository

**Total time:** ~3 hours
**Lines of code:** 3,285
**Files created:** 23

## License & Sharing

This is for personal/educational use. The protocol was reverse engineered from open-source projects and network analysis.

If sharing this project:
- Remove `.env` file (contains your credentials)
- Share the code and documentation
- Credit the open-source projects we used

---

**Status:** Ready to use and extend! 🎉

**Last Updated:** 2025-10-30

# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from datetime import timedelta, datetime
import logging
from typing import Annotated

from langchain_core.tools import tool
from .decorators import log_io
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)


@tool
@log_io
def get_price(
    ticker: Annotated[str, "The ticker symbol of the stock"],
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """
    Get the price data for a given ticker and date range.
    
    Args:
        ticker: The ticker symbol of the stock (e.g., AAPL, MSFT)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        A string containing the price data for the specified ticker and date range
    """
    try:
        stock = yf.Ticker(ticker)
        price_data = stock.history(start=start_date, end=end_date)
        
        if price_data.empty:
            return f"No price data found for {ticker} between {start_date} and {end_date}"
        
        # Format the price data as a string
        result = f"Price data for {ticker} from {start_date} to {end_date}:\n\n"
        for date, row in price_data.iterrows():
            result += f"Date: {date.strftime('%Y-%m-%d')}, Open: {row['Open']:.2f}, High: {row['High']:.2f}, Low: {row['Low']:.2f}, Close: {row['Close']:.2f}, Volume: {row['Volume']}\n"
        
        return result
    except Exception as e:
        error_msg = f"Failed to get price data for {ticker}. Error: {repr(e)}"
        logger.error(error_msg)
        return error_msg
    
@tool
@log_io
def get_simple_moving_average(
    ticker: Annotated[str, "The ticker symbol of the stock"],
    period: Annotated[int, "The period of the moving average"],
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """
    Get the simple moving average for a given ticker and period.
    """
    try:
        stock = yf.Ticker(ticker)
        # Get data for calculating SMA but need extra days before start_date
        
        # Convert string dates to datetime objects
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        # Calculate the adjusted start date for gathering enough data for SMA calculation
        adjusted_start = (start_dt - timedelta(days=period*2)).strftime('%Y-%m-%d')
        
        price_data = stock.history(start=adjusted_start, end=end_date)
        if price_data.empty:
            return f"No price data found for {ticker} between {adjusted_start} and {end_date}"
        
        # Calculate the simple moving average
        sma = price_data['Close'].rolling(window=period).mean()
        
        # Filter to only include data from the requested start_date onwards
        mask = price_data.index >= start_date
        filtered_data = price_data[mask]
        filtered_sma = sma[mask]
        
        # Format the result as a string
        result = f"Simple moving average for {ticker} from {start_date} to {end_date}:\n\n"
        for date, sma_value in zip(filtered_data.index, filtered_sma):
            if not pd.isna(sma_value):  # Skip NaN values
                result += f"Date: {date.strftime('%Y-%m-%d')}, SMA: {sma_value:.2f}\n"
        
        return result
    except Exception as e:
        error_msg = f"Failed to get simple moving average for {ticker}. Error: {repr(e)}"
        logger.error(error_msg)
        return error_msg
    
@tool
@log_io
def get_exponential_moving_average(
    ticker: Annotated[str, "The ticker symbol of the stock"],
    period: Annotated[int, "The period of the moving average"],
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """
    Get the exponential moving average for a given ticker and period.
    """
    try:
        stock = yf.Ticker(ticker)
        # Get data for calculating EMA but need extra days before start_date
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        adjusted_start = (start_dt - timedelta(days=period*2)).strftime('%Y-%m-%d')
        price_data = stock.history(start=adjusted_start, end=end_date)
        if price_data.empty:
            return f"No price data found for {ticker} between {adjusted_start} and {end_date}"
        
        # Calculate the exponential moving average
        ema = price_data['Close'].ewm(span=period, adjust=False).mean()
        
        # Filter to only include data from the requested start_date onwards
        mask = price_data.index >= start_date
        filtered_data = price_data[mask]
        filtered_ema = ema[mask]
        
        # Format the result as a string
        result = f"Exponential moving average for {ticker} from {start_date} to {end_date}:\n\n"
        for date, ema_value in zip(filtered_data.index, filtered_ema):
            if not pd.isna(ema_value):  # Skip NaN values
                result += f"Date: {date.strftime('%Y-%m-%d')}, EMA: {ema_value:.2f}\n"
        
        return result
    except Exception as e:
        error_msg = f"Failed to get exponential moving average for {ticker}. Error: {repr(e)}"
        logger.error(error_msg)
        return error_msg
    